import duckdb
from .utility import get_db_connection
from .db_executor import execute_sql_query
import os



def get_schema_representation(
        db_connection: duckdb.DuckDBPyConnection | None = None,
        db_path: str | None = None,
        # Uppdaterad: include_schemas_and_tables kan vara en dict: {"schema_name": ["table1", "table2_or_None_for_all"]}
        # För nu fokuserar vi på att alltid inkludera specifika scheman helt.
        schemas_to_include: list[str] | None = None, # Ny parameter för att specificera scheman
        format_for_llm: bool = True
) -> str | None:
    """
    Hämtar och formaterar databasschemat (tabeller och kolumner) från specificerade scheman
    för användning med en LLM.
    """
    if not format_for_llm:
        print("VARNING (schema_provider.py): Endast format_for_llm=True är implementerat.")
        return None

    if schemas_to_include is None:
        # Standard scheman som LLM bör känna till för SQL-frågor
        schemas_to_include = ['mart', 'refined'] 
        print(f"INFO (schema_provider.py): Inga specifika scheman angivna, använder standard: {schemas_to_include}")


    conn_provided = db_connection is not None
    conn_to_use = db_connection

    if not conn_to_use:
        if not db_path:
            print("FEL (schema_provider.py): Varken db_connection eller db_path har angetts.")
            return None
        # Kontrollera om db_path existerar innan anslutningsförsök
        if not os.path.exists(db_path):
            print(f"FEL (schema_provider.py): Databasfilen på sökvägen '{db_path}' hittades inte.")
            return None
        print(f"INFO (schema_provider.py): Ingen anslutning angiven, skapar ny från db_path: {db_path}")
        conn_to_use = get_db_connection(db_path, read_only=True)
        if not conn_to_use:
            print(f"FEL (schema_provider.py): Kunde inte skapa databasanslutning från db_path: {db_path}")
            return None

    schema_description_parts = [
        "Du har tillgång till följande tabeller och kolumner i DuckDB-databasen. "
        "Använd fullständiga namn med schema när du skapar SQL-frågor, t.ex. SELECT * FROM schema_namn.tabell_namn;"
        # Tog bort hänvisning till dubbla citationstecken, DuckDB är oftast case-insensitive för okvoterade namn
    ]
    found_any_table = False

    try:
        print(f"INFO (schema_provider.py): Hämtar schema information för scheman: {schemas_to_include}...")

        for current_schema in schemas_to_include:
            schema_exists_df, _ = execute_sql_query(
                conn_to_use, 
                f"SELECT 1 FROM information_schema.schemata WHERE schema_name = '{current_schema}';",
                return_type='dataframe'
            )
            if schema_exists_df is None or schema_exists_df.empty:
                print(f"VARNING (schema_provider.py): Schema '{current_schema}' hittades inte i databasen.")
                continue

            tables_query = f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{current_schema}';"
            tables_df, error = execute_sql_query(conn_to_use, tables_query, return_type='dataframe')

            if error or tables_df is None:
                print(f"FEL (schema_provider.py): Kunde inte hämta tabellista för schema '{current_schema}': {error}")
                continue # Fortsätt till nästa schema

            if tables_df.empty:
                print(f"INFO (schema_provider.py): Inga tabeller hittades i schema '{current_schema}'.")
                continue

            all_table_names_in_schema = tables_df['table_name'].tolist()

            schema_description_parts.append(f"\nSchema: \"{current_schema}\"")

            for table_name in all_table_names_in_schema:
                found_any_table = True
                columns_query = (
                    f"SELECT column_name, data_type FROM information_schema.columns "
                    f"WHERE table_name = '{table_name}' AND table_schema = '{current_schema}' "
                    f"ORDER BY ordinal_position;"
                )
                columns_df, col_error = execute_sql_query(conn_to_use, columns_query, return_type='dataframe')

                if col_error or columns_df is None or columns_df.empty:
                    print(f"VARNING (schema_provider.py): Kunde inte hämta kolumner för tabell {current_schema}.{table_name}: {col_error}")
                    schema_description_parts.append(f"  Tabell: \"{table_name}\" (kunde inte hämta kolumndetaljer)")
                    continue

                table_desc = f"  Tabell: \"{table_name}\"\n  Kolumner:"
                for _, row in columns_df.iterrows():
                    table_desc += f"\n    - \"{row['column_name']}\" (Typ: {row['data_type']})"
                schema_description_parts.append(table_desc)

        if not found_any_table:
            print("VARNING (schema_provider.py): Inga tabeller att processera hittades i de specificerade schemana.")
            # Returnera en sträng som indikerar detta, istället för None, så LLM får veta det.
            return "Inga tabeller hittades i de relevanta databasschemana ('mart', 'refined'). Kontrollera att dbt-modellerna har körts korrekt."

        full_schema_description = "\n".join(schema_description_parts)
        print(f"INFO (schema_provider.py): Schema representation skapad (början):\n{full_schema_description[:500]}...")
        return full_schema_description

    except duckdb.Error as e:
        print(f"FEL (schema_provider.py): DuckDB-fel vid hämtning av schema: {e}")
        return "Ett DuckDB-fel uppstod vid hämtning av schemat." # Ge ett meddelande till LLM
    except Exception as e:
        print(f"FEL (schema_provider.py): Oväntat fel vid hämtning av schema: {e}")
        import traceback
        traceback.print_exc() # För mer detaljerad loggning
        return "Ett oväntat fel uppstod vid hämtning av schemat." # Ge ett meddelande till LLM
    finally:
        if not conn_provided and conn_to_use:
            print("INFO (schema_provider.py): Stänger databasanslutning som skapades internt.")
            conn_to_use.close()