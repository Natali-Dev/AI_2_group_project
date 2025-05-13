import duckdb
import os


# Sökväg till databasen
data_folder = 'data'
db_file_name =  'job_embeddings.duckdb'
db_path = os.path.join(data_folder, db_file_name)

print(f"Försöker ansluta till/skapa DuckDB-databasen: {db_path}")
con = duckdb.connect(database=db_path, read_only=False)

# Installera och ladda VSS-tillägget. (Behövs bara köras en gång för att installera)
try:
    con.sql("INSTALL vss;")
    print("VSS-tillägget är nu installerat")
except Exception as e:
    print(f"VSS-tillägget kunde inte installeras. Kanske redan är installerat?: {e}")

try:
    con.sql("LOAD vss;")
    print("VSS-tillägget laddat.")
except Exception as e:
    print(f"Kunde inte ladda VSS-tillägget: {e}. Kontrollera att det är installerat.")


# Embedding-dimension. all-MiniLM-L6-v2.
embedding_dim = 384

# Skapa tabell för text-chunks och deras embeddings
try:
    con.sql(f"""
            CREATE TABLE IF NOT EXISTS job_chunks(
            job_id VARCHAR,                     -- ID från ursprunglig jobbannons
            chunk_id INTEGER,                   -- Unikt ID för denna chunk inom en jobbannons
            chunk_text VARCHAR,                 -- Text för denna chunk
            embedding FLOAT[{embedding_dim}],   -- Embedding för denna chunk
            PRIMARY KEY (job_id, chunk_id)      -- Om chunk_id är globalt unikt räcker det med chunk_id
            );
            """)
    print(f"Tabellen 'job_chunks med embedding-dimension {embedding_dim} är redo.")
except Exception as e:
    print(f"Kunde inte skapa tabellen 'job_chunks': {e}")

con.close()
print("Databasanslutning stängd")


