import duckdb
import os
import pandas as pd
from sentence_transformers import SentenceTransformer

# --- Konfiguration ---
source_db_path = 'ads_data.duckdb'
source_schema_name = 'staging'
source_table_name = 'job_ads'

job_id_column_in_source = 'id'

text_column_to_embed_in_source = 'description__text'

embedding_db_folder = 'data'
embedding_db_file_name = 'job_embeddings.duckdb'
embedding_db_path = os.path.join(embedding_db_folder, embedding_db_file_name)

model_name = 'all-MiniLM-L6-v2'

# --- Slut på konfiguration ---


# Ladda embedding-modellen
print (f"Laddar embedding-modell: {model_name}...")
try:
    embed_model = SentenceTransformer(model_name)
except Exception as e:
    print(f"FEL: Kunde inte ladda SenteneTransformer-modell ('{model_name}).")
    print(f"Kontrollera att biblioteket är installerat (uv pip install sentence-transformers) och att modellen är giltig.")
    print(f"FEL: {e}")
    exit()
print("Modell är laddad.")

# Anslut till käll-databasen (ads_data.duckdb)
print (f"Ansluter till käll-databasen: {source_db_path}...")
try:
    source_con = duckdb.connect(database= source_db_path, read_only=True)
except Exception as e:
    print(f"FEL: Kunde inte ansluta till käll-databasen ('{source_db_path}'). Har du kört extract_load_api.py?")
    print(f"FEL: {e}")
    exit()

# Hämta data från källtbellen
sql_query = f"SELECT \"{job_id_column_in_source}\", \"{text_column_to_embed_in_source}\" FROM \"{source_schema_name}\".\"{source_table_name}\";"
print(f"Hämtar data från '{source_schema_name}'. '{source_table_name}' med SQL: {sql_query}")
try:
    job_ads_df = source_con.execute(sql_query).fetchdf()
    source_con.close()
    print(f"Data är hämtad, {len(job_ads_df)} rader.")
    
    if job_ads_df.empty:
        print(f"Ingen data hittades i '{source_schema_name}'. '{source_table_name}'. Kontrollera kolumnnamn samt att extract_load_api.py har körts.")
        exit()
    
    if job_id_column_in_source not in job_ads_df.columns:
        print(f"FEL Kolunmen '{job_id_column_in_source}' hittades inte i '{source_schema_name}'. '{source_table_name}'.")
        print(f"Tillgängliga kolumner: {job_ads_df.columns}")
        exit()

        job_ads_df.dropna(subset=[text_column_to_embed_in_source], inplace=True)
        job_ads_df = job_ads_df[job_ads_df[text_column_to_embed_in_source].astype(str).str.strip() != '']
except Exception as e:
    print(f"FEL: Kunde inte hämta data från '{source_schema_name}'. '{source_table_name}: {e}")
    print(f"Kontrollera att tabellen och kolumerna ('{job_id_column_in_source}' och '{text_column_to_embed_in_source}') existerar i {source_db_path} under schemat {source_schema_name}.")
    source_con.close()
    exit()

if job_ads_df.empty:
    print("Ingen data att bearbeta efter filtrering av tomma textfält")
    exit()


# Anslut till mål-databasen (för embeddings specifikt)
print(f"Ansluter till embedding-databasen: {embedding_db_path}...")
embedding_con = duckdb.connect(database=embedding_db_path, read_only=False)
try:
    embedding_con.sql("BEGIN TRANSACTION;")
except Exception as e:
    print(f"VARINNG: Kunde inte ladda VSS-tillägget i {embedding_db_path}. Fel: {e}")

# Hämta nästa tillgängliga globaka chunk_id
try:
    current_max_chunk_id = embedding_con.execute("SELECT COALESCE(MAX(chunk_id),)")