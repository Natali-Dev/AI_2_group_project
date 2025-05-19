import duckdb
import os
import pandas as pd

db_file_path = r'C:\Users\edwin\Documents\data-engineering-project\AI_2_group_project\ads_data.duckdb'

try:
    con = duckdb.connect(database=db_file_path, read_only=True)
    print(f"Ansluten till databasen: {db_file_path}")

    print("\nTillgängliga scheman: ")
    schemas_df = con.sql("SHOW SCHEMAS;").df()
    print(schemas_df)

    print("\nTabeller i 'stating'-schemat: ")
    staging_tables_df = con.sql("SHOW TABLES FROM staging;").df()
    print(staging_tables_df)

    try:
        print("\nTabeller i 'main'-schemat (dbt-modeller): ")
        main_tables_df = con.sql("SHOW TABLES FROM main;").df()
        print(main_tables_df)
        
        if not main_tables_df[main_tables_df['name'] == 'dim_job_details'].empty:
            print("\nFörsta 5 raderna från main.dim_job_details: ")
            dim_details_sample_df = con.sql("SELECT * FROM main.dim_job_details LIMIT 5;").df()
            print(dim_details_sample_df)
        else:
            print("\Tabellen 'main.dim_job_details' finns inte i 'main'-schemat.")
    except duckdb.CatalogException as e:
        print(f"\nKunde inte lista tabeller från'main'-schemat (kanske inte finns eller är tomt): {e}")
    
    if not staging_tables_df[staging_tables_df['name'] == 'job_ads'].empty:
        print("\nFörsta 5 raderna från staging.job_ads: ")
        dlt_output_sample_df = con.sql("SELECT id, headline, _dlt_load_id FROM staging.job_ads LIMIT 5;").df()
        print(dlt_output_sample_df)
    else:
        print("\nTabellen 'staging.job_ads' finns inte i 'staging'-schemat")

except duckdb.DatabaseError as e:
    print(f"Fel vid anslutning till databasen:")
finally:
    if 'con' in locals() and con:
        con.close()
        print("\nDatabasanslutning stängd.")