import duckdb
import os

def get_db_connection(db_path: str, read_only: bool = True) -> duckdb.DuckDBPyConnection | None:
    """
    Etablrear och returnerar en ansltning till DuckDB-databasen.
    Försöker konstruera en absolut sökväg om db_path är relativ från projektets rot.
    """
    actual_db_path = db_path
    if not os.path.isabs(db_path):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        actual_db_path = os.path.join(project_root, db_path)
    try:
        if not os.path.exists(actual_db_path):
            print(f"FEL i get_db_connecton: Databasfilen hittades inte på: {actual_db_path}")
            return None
        connection = duckdb.connect(database=actual_db_path, read_only=read_only)
        return connection
    except duckdb.Error as e:
        print(f"FEL i get_db_connecton: Kunde inte ansluta till databasen på {actual_db_path}: {e}")
        return None