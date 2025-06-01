import duckdb
import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np # Kan behövas för vissa operationer med embeddings

# --- Konfiguration ---
# Källdatabas (där dina fullständiga jobbannonser finns)
# Denna ska peka på ads_data.duckdb direkt i projektmappen
source_db_path = 'ads_data.duckdb' # Ligger i projektroten

# Schema och tabell i källdatabasen som innehåller texten att embedda
source_schema_name = 'mart' 
source_table_name = 'mart_ads'  # mart_ads innehåller en 'description'-kolumn

# Kolumnnamn i källtabellen (mart.mart_ads)
# 'id' finns inte direkt i mart_ads, men vi behöver ett unikt ID per annons.
# fct_job_ads har 'job_details_id' som kan vara ett bra ID.
# Om mart_ads är byggd på fct_job_ads, kan den innehålla ett motsvarande ID.
# Vi antar här att 'headline' + 'employer_name' kan ge en form av unikhet,
# eller så använder vi ett löpnummer om inget bra ID finns i mart_ads.
# Bäst vore om mart_ads hade ett tydligt 'job_ad_id'.
# För nu, låt oss använda 'headline' som en proxy för ID, eller så måste du se till att du har ett ID.
# Om 'mart_ads' har en unik nyckel (t.ex. från 'fct_job_ads.job_details_id'), använd den.
# Låt oss anta att 'headline' kan fungera som en job_id för detta exempel,
# eller om du har en bättre unik identifierare i mart_ads, använd den.
# Om du har en 'job_details_id' eller liknande i mart_ads, använd den!
# Vi tar 'headline' som exempel, men du kanske behöver justera detta.
job_id_column_in_source = 'headline' # ANPASSA OM DU HAR ETT BÄTTRE ID I mart_ads
                                    # t.ex. om 'job_details_id' finns i mart_ads

text_column_to_embed_in_source = 'description' # Kolumnen med den långa beskrivningstexten

# Måldatabas (för embeddings)
embedding_db_folder = 'data' # Denna ligger i en undermapp
embedding_db_file_name = 'job_embeddings.duckdb'
embedding_db_path = os.path.join(embedding_db_folder, embedding_db_file_name)

# Embedding-modell
model_name = 'all-MiniLM-L6-v2' # 384 dimensioner

# Chunking-parametrar
CHUNK_SIZE = 500  
CHUNK_OVERLAP = 50 
# --- Slut på konfiguration ---

def simple_text_splitter(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Enkel textdelare baserad på tecken med överlapp."""
    if not text or not isinstance(text, str):
        return []
    
    chunks = []
    current_position = 0
    text_len = len(text)
    
    while current_position < text_len:
        end_position = min(current_position + chunk_size, text_len)
        chunks.append(text[current_position:end_position])
        current_position += (chunk_size - chunk_overlap)
        if current_position >= text_len and end_position < text_len : # Säkerställ att sista biten tas med om överlapp hoppar över slutet
            if text[end_position-(chunk_size-chunk_overlap):] not in chunks[-1] and len(text[end_position-(chunk_size-chunk_overlap):]) > chunk_overlap: # undvik för korta/identiska sista bitar
                 remaining_start = end_position-(chunk_size-chunk_overlap) if end_position-(chunk_size-chunk_overlap) > 0 else 0
                 if len(text[remaining_start:]) >0: # lägg bara till om det finns text kvar
                    chunks.append(text[remaining_start:])

    # Ta bort eventuella helt tomma chunks som kan ha skapats
    return [c for c in chunks if c.strip()]


def main():
    print(f"INFO: Startar populate_embeddings.py...")

    # Ladda embedding-modellen
    print(f"INFO: Laddar embedding-modell: {model_name}...")
    try:
        embed_model = SentenceTransformer(model_name)
        embedding_dim_for_table = embed_model.get_sentence_embedding_dimension()
        print(f"INFO: Modell '{model_name}' (dimension: {embedding_dim_for_table}) är laddad.")
    except Exception as e:
        print(f"FEL: Kunde inte ladda SentenceTransformer-modell ('{model_name}').")
        print(f"      Kontrollera att biblioteket är installerat (pip install sentence-transformers) och att modellen är giltig.")
        print(f"      Felmeddelande: {e}")
        return

    # Anslut till käll-databasen (ads_data.duckdb)
    print(f"INFO: Ansluter till käll-databasen: {source_db_path}...")
    if not os.path.exists(source_db_path):
        print(f"FEL: Käll-databasfilen hittades inte på: {source_db_path}")
        print(f"      Kontrollera sökvägen och att dbt har byggt denna databas (t.ex. ads_data.duckdb).")
        return
        
    try:
        source_con = duckdb.connect(database=source_db_path, read_only=True)
    except Exception as e:
        print(f"FEL: Kunde inte ansluta till käll-databasen ('{source_db_path}').")
        print(f"      Felmeddelande: {e}")
        return

    # Hämta data från källtabellen
    # Anpassa frågan om ditt schema eller tabellnamn är annorlunda.
    # Använd citationstecken om dina kolumnnamn/tabellnamn innehåller specialtecken eller är reserverade ord.
    # sql_query = f"SELECT \"{job_id_column_in_source}\", \"{text_column_to_embed_in_source}\" FROM \"{source_table_name}\";"
    # Om du använder ett schema i källan:
    sql_query = f"SELECT \"{job_id_column_in_source}\", \"{text_column_to_embed_in_source}\" FROM \"{source_schema_name}\".\"{source_table_name}\";"

    print(f"INFO: Hämtar data från '{source_schema_name}'.'{source_table_name}' med SQL: {sql_query}")
    try:
        job_ads_df = source_con.execute(sql_query).fetchdf()
        print(f"INFO: Data hämtad, {len(job_ads_df)} rader initialt.")
        
        if job_ads_df.empty:
            print(f"VARNING: Ingen data hittades i '{source_schema_name}'.'{source_table_name}'. Avbryter.")
            source_con.close()
            return
        
        if job_id_column_in_source not in job_ads_df.columns:
            print(f"FEL: Kolumnen '{job_id_column_in_source}' hittades inte i resultatet.")
            print(f"      Tillgängliga kolumner: {job_ads_df.columns.tolist()}")
            source_con.close()
            return

        if text_column_to_embed_in_source not in job_ads_df.columns:
            print(f"FEL: Kolumnen '{text_column_to_embed_in_source}' hittades inte i resultatet.")
            print(f"      Tillgängliga kolumner: {job_ads_df.columns.tolist()}")
            source_con.close()
            return

        # Rensa data: ta bort rader där textkolumnen är null/tom
        job_ads_df.dropna(subset=[text_column_to_embed_in_source], inplace=True)
        job_ads_df = job_ads_df[job_ads_df[text_column_to_embed_in_source].astype(str).str.strip() != '']
        print(f"INFO: Antal rader efter rensning av tomma textfält: {len(job_ads_df)}.")

    except Exception as e:
        print(f"FEL: Kunde inte hämta eller bearbeta data från '{source_schema_name}'.'{source_table_name}': {e}")
        source_con.close()
        return
    finally:
        source_con.close() # Se till att källanslutningen alltid stängs

    if job_ads_df.empty:
        print("INFO: Ingen data att bearbeta efter filtrering. Avslutar.")
        return

    # Anslut till/skapa mål-databasen för embeddings
    print(f"INFO: Ansluter till/skapar embedding-databasen: {embedding_db_path}...")
    os.makedirs(embedding_db_folder, exist_ok=True) # Skapa mappen om den inte finns
    embedding_con = duckdb.connect(database=embedding_db_path, read_only=False)

    try:
        # Skapa tabellen om den inte finns (gör skriptet mer robust)
        # chunk_id sätts som PRIMARY KEY för global unikhet.
        embedding_con.sql(f"""
            CREATE TABLE IF NOT EXISTS job_chunks(
                job_id VARCHAR,
                chunk_id INTEGER PRIMARY KEY, 
                chunk_text VARCHAR,
                embedding FLOAT[{embedding_dim_for_table}]
            );
        """)
        print(f"INFO: Tabellen 'job_chunks' är redo i {embedding_db_path}.")

        # Hämta nästa tillgängliga globala chunk_id
        result = embedding_con.execute("SELECT COALESCE(MAX(chunk_id), 0) FROM job_chunks;").fetchone()
        current_max_chunk_id = result[0] if result else 0
        next_chunk_id_to_assign = current_max_chunk_id + 1
        print(f"INFO: Högsta befintliga chunk_id: {current_max_chunk_id}. Nästa tilldelade chunk_id startar från: {next_chunk_id_to_assign}")

        embedding_con.sql("BEGIN TRANSACTION;")
        print("INFO: Startar databastransaktion.")

        chunks_processed_total = 0
        for index, row in job_ads_df.iterrows():
            current_job_id = str(row[job_id_column_in_source])
            text_to_embed = str(row[text_column_to_embed_in_source]) # Säkerställ sträng

            text_chunks = simple_text_splitter(text_to_embed, CHUNK_SIZE, CHUNK_OVERLAP)

            if not text_chunks:
                print(f"VARNING: Inga text-chunks skapades för job_id {current_job_id} (texten kan vara för kort eller tom).")
                continue
            
            num_chunks_for_job = 0
            for chunk_content in text_chunks:
                try:
                    chunk_embedding_vector = embed_model.encode(chunk_content)
                    
                    embedding_con.execute(
                        "INSERT INTO job_chunks (job_id, chunk_id, chunk_text, embedding) VALUES (?, ?, ?, ?);",
                        [current_job_id, next_chunk_id_to_assign, chunk_content, chunk_embedding_vector.tolist()]
                    )
                    num_chunks_for_job += 1
                    next_chunk_id_to_assign += 1
                except Exception as e_embed_insert:
                    print(f"FEL: Kunde inte skapa embedding eller infoga chunk för job_id {current_job_id}, chunk_id {next_chunk_id_to_assign} (hoppar över denna chunk): {e_embed_insert}")
            
            chunks_processed_total += num_chunks_for_job
            if (index + 1) % 20 == 0: # Logga framsteg var 20:e annons
                print(f"INFO: Bearbetat {index+1}/{len(job_ads_df)} jobbannonser. Totalt {chunks_processed_total} chunks infogade...")

        embedding_con.sql("COMMIT;")
        print(f"INFO: Transaktion committad. Totalt {chunks_processed_total} chunks och embeddings har infogats i '{embedding_db_path}'.")

    except Exception as e:
        print(f"FEL: Ett fel inträffade under bearbetning av embeddings: {e}")
        try:
            embedding_con.sql("ROLLBACK;")
            print("INFO: Transaktion tillbakadragen på grund av fel.")
        except Exception as er:
            print(f"FEL: Kunde inte rulla tillbaka transaktion: {er}")
    finally:
        embedding_con.close()
        print("INFO: Anslutning till embedding-databasen är stängd.")
    
    print("INFO: populate_embeddings.py har slutförts.")

if __name__ == "__main__":
    main()