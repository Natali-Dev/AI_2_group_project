import pandas as pd
import duckdb
from .utility import get_db_connection



def execute_sql_query(
        db_connection: duckdb.DuckDBPyConnection | None = None,
        sql_query: str | None = None,
        db_path: str | None = None,
        return_type: str = "dataframe"

) -> tuple[pd.DataFrame | list[dict] | None, str | None]:
    """
    Kör en SQL-fråga mot den angivna databasen och returnera resultatet.
    Hanterar anslutningsskapande om ingen befintilig anslutning ges.

    Args:
        db_connection: En befintlig DuckDB-anslutning (valfri)
        sql_query: SQL-frågan som ska köras.
        db_path: Sökväg till databasfilen (används om db_connection är None)
        return_type: Format för resultatet ('dataframe' eller 'list_of_dicts')

    Returns:
        En tuple med (resultat, felmeddelande). Resultatet är None om ett fel uppstår.
        Felmeddelandet är None om inget fel inträffarr.
    """
    if not sql_query or not sql_query.strip():
        varning_msg = "VARNING (db_executor.py): Tom SQL-fråga mottagen."
        print(varning_msg)
        # Returnera tom DataFrame eller tom lista beroende på return_type
        if return_type == "dataframe":
            return pd.DataFrame(), varning_msg
        else:
            return [], varning_msg

    conn_provided = db_connection is not None
    conn_to_use = db_connection

    if not conn_to_use:
        if not db_path:
            error_msg = "FEL (db_executor.py): Varken db_connection eller db_path har angetts."
            print(error_msg)
            return None, error_msg
        print(f"INFO (db_executor.py): Ingen anslutning angiven, skapar ny från db_path: {db_path}")
        conn_to_use = get_db_connection(db_path, read_only=True) #SQL SELECt är read-only
        if not conn_to_use:
            error_msg =f"FEL (db_executor.py): Kunde inte skapa databasanslutning från db_path: {db_path}"
            print(error_msg)
            return None, error_msg
    
    try:
        print(f"INFO (db_executor.py): Exekverar SQL-frågan: {sql_query[:200]}...")
        if return_type == "dataframe":
            result_df = conn_to_use.execute(sql_query).fetchdf()
            print(f"INFO (db_executor.py):SQL-frågan exekverad, returnerade{len(result_df)} rader.")
            return result_df, None
        elif return_type == "list_of_dicts":
            result_list = conn_to_use.execute(sql_query).fetchall()
            # Konvertera från lista av tupler till lista av dicts om det behövs( neroende på DuckDB-version/inställningar
            # För nyare versioner kan .arrow() eller .df().to_dict('records') vara effektivare"
            # fetchall() returnerar tupler, så vi behöver kolumndata för att skapa dicts
            columns = [desc[0] for desc in conn_to_use.description]
            result_list_of_dicts = [dict(zip(columns, row)) for row in result_list]
            print(f"INFO (db_executor.py):SQL-frågan exekverad, returnerade{len(result_list_of_dicts)} rader som list of dicts.")
            return result_list_of_dicts, None
        else:
            error_msg = f"FEL (db_executor.py): Okänd return_type: {return_type}"
            print(error_msg)
            return None, error_msg
    except duckdb.Error as e:
        error_msg = f"FEL db_executor.py: DuckDB-fel vid exekvering av SQL: {e}\Fråga: {sql_query}"
        print(error_msg)
        return None, str(e)
    except Exception as e:
        error_msg = f"FEL (db_connection): Oväntat fel vid exekvering av SQL: {e}nFråga: {sql_query}"
        print(error_msg)
        return None, str(e)
    finally:
        if not conn_provided and conn_to_use:
            print("INFO (db_executor.py): Stänger databasanslutning som skapades internt.")
            conn_to_use.close()