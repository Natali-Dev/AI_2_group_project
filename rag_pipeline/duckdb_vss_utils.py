import duckdb
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import traceback # För bättre felutskrift

# Importera Document-objektet.
try:
    from langchain_core.documents import Document
except ImportError:
    print("VARNING (duckdb_vss_utils.py): Kunde inte importera 'Document' från 'langchain_core.documents'. Använder fallback-klass.")
    class Document:
        def __init__(self, page_content, metadata=None):
            self.page_content = page_content
            self.metadata = metadata if metadata is not None else {}
        def __repr__(self):
            return f"Document(page_content='{self.page_content[:50]}...', metadata={self.metadata})"

# Ladda embedding-modellen.
MODEL_NAME = 'all-MiniLM-L6-v2'
embedding_model = None
try:
    print(f"INFO (duckdb_vss_utils.py): Laddar sentence transformer-modell: {MODEL_NAME}...")
    embedding_model = SentenceTransformer(MODEL_NAME)
    print(f"INFO (duckdb_vss_utils.py): Sentence transformer-modell '{MODEL_NAME}' laddad.")
except Exception as e:
    print(f"FEL (duckdb_vss_utils.py): Kunde inte ladda sentence transformer-modellen '{MODEL_NAME}': {e}")
    embedding_model = None

def get_query_embedding(query_text: str):
    """Genererar en embedding för den givna frågetexten."""
    if embedding_model is None:
        print("FEL (duckdb_vss_utils.py): Embedding-modellen är inte tillgänglig för get_query_embedding.")
        return None
    try:
        embedding = embedding_model.encode(query_text)
        return embedding
    except Exception as e:
        print(f"FEL (duckdb_vss_utils.py): Kunde inte generera query-embedding: {e}")
        return None

def get_similar_docs_duckdb(db_path: str, query_text: str, k: int = 15, embedding_dim: int = 384):
    """
    Ansluter till DuckDB-databasen, skapar embedding för frågan, utför en VSS-sökning,
    och returnerar de k mest lika dokument-chunkarna.
    """
    if not db_path:
        print("FEL (duckdb_vss_utils.py): Databassökväg saknas för get_similar_docs_duckdb.")
        return []
    if not os.path.exists(db_path):
        print(f"FEL (duckdb_vss_utils.py): Databasfilen hittades inte på: {db_path}")
        return []

    if embedding_model is None:
        print("FEL (duckdb_vss_utils.py): Embedding-modellen är inte laddad, kan inte utföra RAG-sökning.")
        return []
        
    query_embedding = get_query_embedding(query_text)
    if query_embedding is None:
        print("FEL (duckdb_vss_utils.py): Kunde inte skapa embedding för frågan, avbryter RAG-sökning.")
        return []

    # Säkerställ att embeddingen är en NumPy array av typen float32 innan konvertering till lista
    if not isinstance(query_embedding, np.ndarray):
        query_embedding = np.array(query_embedding, dtype=np.float32)
    elif query_embedding.dtype != np.float32:
        query_embedding = query_embedding.astype(np.float32)
    
    query_embedding_list = query_embedding.tolist()

    similar_docs_list = []
    con = None
    
    try:
        print(f"INFO (duckdb_vss_utils.py): Ansluter till DuckDB (read-only): {db_path}")
        con = duckdb.connect(database=db_path, read_only=True)
        
        # Försök ladda VSS-tillägget. Om det misslyckas, försök installera det.
        try:
            print("INFO (duckdb_vss_utils.py): Försöker ladda VSS-tillägget...")
            con.execute("LOAD vss;")
            print("INFO (duckdb_vss_utils.py): VSS-tillägg laddat i anslutningen.")
        except Exception as e_load:
            print(f"VARNING (duckdb_vss_utils.py): Kunde inte ladda VSS-tillägget explicit: {e_load}. Försöker installera...")
            try:
                # Stäng read-only anslutningen och öppna en ny för att kunna installera
                if con: con.close()
                con_rw = duckdb.connect(database=db_path, read_only=False) # Behöver read-write för INSTALL
                print("INFO (duckdb_vss_utils.py): Försöker installera VSS-tillägget...")
                con_rw.execute("INSTALL vss;")
                con_rw.execute("LOAD vss;") # Ladda direkt efter installation
                print("INFO (duckdb_vss_utils.py): VSS-tillägg installerat och laddat.")
                con_rw.close()
                # Återanslut i read-only mode
                con = duckdb.connect(database=db_path, read_only=True)
                con.execute("LOAD vss;") # Ladda igen i den nya read-only anslutningen
                print("INFO (duckdb_vss_utils.py): Återansluten med VSS laddat.")
            except Exception as e_install:
                print(f"FEL (duckdb_vss_utils.py): Kunde inte installera eller ladda VSS-tillägget: {e_install}. "
                      "array_distance kommer troligen att misslyckas.")
                # Om VSS inte kan laddas alls är det ingen idé att fortsätta med VSS-specifik fråga
                if con: con.close()
                return []


        # Bygg SQL-frågan som en enda sträng
        # Använder nu list_value(?) som DuckDB föredrar för listparametrar i nyare versioner
        # och CAST för att säkerställa typen.
        sql_query_for_rag = f"""
            SELECT job_id, chunk_id, chunk_text, 
                   array_distance(embedding, CAST(? AS FLOAT[{embedding_dim}])) AS distance 
            FROM job_chunks 
            ORDER BY distance 
            LIMIT ?;
        """
        
        print(f"INFO (duckdb_vss_utils.py): Exekverar RAG SQL med parametrar.")
        
        prepared_statement = con.execute(sql_query_for_rag, [query_embedding_list, k])
        results = prepared_statement.fetchall()
        
        print(f"INFO (duckdb_vss_utils.py): Hittade {len(results)} dokument i DuckDB för RAG.")

        for row in results:
            job_id, chunk_id, chunk_text, distance = row
            doc = Document(
                page_content=chunk_text,
                metadata={
                    "job_id": str(job_id) if job_id is not None else "Okänt JobbID", 
                    "chunk_id": int(chunk_id) if chunk_id is not None else -1, 
                    "source": f"duckdb://job_id={job_id}/chunk_id={chunk_id}",
                    "distance": float(distance) if distance is not None else float('inf')
                }
            )
            similar_docs_list.append(doc)

    except duckdb.BinderException as e_binder:
        print(f"FEL (duckdb_vss_utils.py): Binder Error under DuckDB likhetssökning: {e_binder}")
        traceback.print_exc()
    except TypeError as e_type: # Fånga specifikt TypeError för execute()
        print(f"FEL (duckdb_vss_utils.py): TypeError vid con.execute(): {e_type}")
        print("      Detta kan bero på felaktigt antal eller typ av argument till execute().")
        print(f"      Försökte köra: {sql_query_for_rag if 'sql_query_for_rag' in locals() else 'SQL-fråga ej definierad'}")
        print(f"      Med parametrar: {[query_embedding_list if 'query_embedding_list' in locals() else 'Param1 ej def', k if 'k' in locals() else 'Param2 ej def']}")
        traceback.print_exc()
    except Exception as e_general:
        print(f"FEL (duckdb_vss_utils.py): Oväntat fel under DuckDB likhetssökning: {e_general}")
        traceback.print_exc()
    finally:
        if con:
            con.close()
            print(f"INFO (duckdb_vss_utils.py): Anslutning till {db_path} stängd.")
            
    return similar_docs_list

