import pandas as pd
import duckdb

def execute_query(sql_query: str, db_path: str) -> pd.DataFrame | None:
    """
    Kör en SQL-fråga mot den angivna databasen och returnera resultatet som en pandas DataFrame.
    """
    if not sql_query or not sql_query.strip():
        print("VARNING (db_executor.py): Tom SQL-fråga mottagen.")
        return pd.DataFrame()
    conn = get_db_connection(db_path, read_only=True)
    