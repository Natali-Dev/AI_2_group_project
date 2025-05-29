import duckdb
from .utility import get_db_connection
from .db_executor import execute_sql_query


def get_schem_representation(
        db_connection: duckdb.DuckDBPyConnection | None = None,
        db_path: str | None = None,
        include_tables: list[str] | None = None,
        format_for_llm: bool = True

) -> str | None:
    """
    Hämatr och formaterar databasschemat (tabeller och kolumner) för användning med en LLM.

    Args:
        db_connection: En befintlig DuckDB-anslutning
        db_path: Sökväg till databasfilen (används om db_connection är None).
        include_tables: En lista med tabellnamn att specifikt inkludera. Om None, inkluderas alla.
        format_for_llm: Om True, formaterar output som en textbeskrivning lämplig fr en LLM-prompt.
                        Annars returneras en mer strukturerad dictionary (ej implementerat än).
    Returns:
        En strängbeskrivning av schemat, eller None om ett fel inträffar.
    
    """
    if not format_for_llm:
        # TODO: Implementera return av en strukturerad dictionary om det behöbs senare
        print("VARNING (schema_provider.py): Endsat format_for_llm=True är implementerat.")
        return None
    conn_provided = db_connection is not None
    conn_to_use = db_connection

    if not conn_to_use:
        if not db_path:
            print("FEL (schema_provider.py): Varken db_connection eller db_path har angetts")
            return None
        print(f"INFO (schema_provider.py): Ingen anslutning angiven, skapa ny från db_path: {db_path}")
        conn_to_use = get_db_connection(db_path, read_only= True)
        if not conn_to_use:
            print(f"FEL (schema_provider.py): Kunde inte skapa databasanslutning från db_path: {db_path}")
            return None
        
    schema_description_parts = []

    try:
        print("INFO (schema_provider.py): Hämtar schema information...")
        # Hämta alla tabeller och vyer i huvudschemat ('main' flr DuckDB per default)
        tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main';"
        tables_df, error = execute_sql_query(conn_to_use, tables_query, return_type= 'dataframe')
        if error or tables_df is None:
            print(f"FEL (schema_provider.py): Kunde inte hämta tabellista: {error}")
            return None
        

        all_tables_names = tables_df['table_name'].tolist()

        tables_to_process = []
        if include_tables:
            # Filtrera för att bara inkludera specifika tabeller som faktistk finns
            for t_name in include_tables:
                if t_name in all_tables_names:
                    tables_to_process.append(t_name)
                else:
                    print(f"VARNING (schema_provider.py): Tabell '{t_name}' specifierad i include_tables men finns inte i databasen.")
        else:
            tables_to_process = all_tables_names
        
        if not tables_to_process:
            print("VARNING (schema_provider.py): Inga tabeller att processera för schemat.")
            return "Inga tabeller hittades eller specifierades för schemat."
        
        schema_description_parts.append(
            "Du har tillgång till följande tabeller och kolumner i DuckDB-databasen( använda dubbla citationstecken runt tabell- och kolumnnamn vid behöv, t.ex. \"tabel_name\".\"column_Name\)"
        )

        for table_name in tables_to_process:
            # Använd PRAGMA table_info('table_name') för att få kolumner och typer.
            # Eller information_schema.columns
            columns_query = f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}' AND table_schema = 'main' ORDER BY ordanial_position;"
            columns_df, col_error = execute_sql_query(conn_to_use, columns_query, return_type ='dataframe')

            if col_error or columns_df is None or columns_df.empty:
                print(f"VARNING (schema_provider.py): Kunde inte hämta koluner för tabell {table_name}:{col_error}")
                schema_description_parts.append(f"nTabell: \"{table_name}\" (kunde inte hämta kolumndetaler)")
                continue

            table_desc = f"\nTabell: \"{table_name}\"\nKolumner:"
            for _, row in columns_df.iterrows():
                table_desc += f"\n - \"{row['column_name']}\" (Typ: {row['data_type']})"
            schema_description_parts.append(table_desc)
        full_schema_description = "\n".join(schema_description_parts)
        print(f"INFO (schema_provicder.py): Schema representation skapad:\n{full_schema_description[500]}...")
        return full_schema_description
    except duckdb.Error as e:
        print(f"FEL (schema_provider.py): DuckDB-fel vid hämtning av schema: {e}")
        return None
    except Exception as e:
        print(f"FEL (schema_provider.py): Oväntat fel vid hämtning av schema: {e}")
        return None
    finally:
        if not conn_provided and conn_to_use:
            print("INFO (schema_provider.py): Stänger databasanslutning som skapades internt.")
            conn_to_use.close()