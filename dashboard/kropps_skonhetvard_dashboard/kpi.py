import duckdb
import os 
from pathlib import Path
import pandas as pd


working_directory = Path(__file__).parents[0]
os.chdir(working_directory)
with duckdb.connect("ads_data.duckdv") as connection:
    df_mart = connection.execute("SELECT * FROM mart.mart_kroopps_skonhet").df()

    # Count total number of vacancies
    def total_vacancies(df: pd.DataFrame):
        return df["vacancies"].sum()
    
    # most common occupations in the field
    def top_occupations(df: pd.DataFrame, n: int = 5):
        return df["occupation"].value_counts().head(n).reset_index()
    
    # count total number of jobs per city
    def vacancies_per_city (df: pd.DataFrame):
        return df(
            df.groupby("workplace_city")["vacancies"]
            .sum().reset_index()
            .rename(columns={"workplace_city": "Stad", "vacancies": "Antal jobb"})
        )
    
    # pick out the biggest employers in the field
    def top_employers(df: pd.DataFrame):
        return df["employer_name"].value_counts().head(5).reset_index()
    
    # jobs per field
    def occupations_group_counts(df: pd.DataFrame):
        return df.groupby["occupation_group"].value_counts().reset_index()
    

    # get information about the attributes required for a job
    def get_attributes_per_field(df: pd.DataFrame):
        return df[["experience_required", "driving_license", "access_to_own_car"]].sum().reset_index().rename(
            columns={
                "experience_required": "Erfarenhet",
                "driving_license": "Körkort",
                "access_to_own_car": "Tillgång till egen bil"
            }
        )
        
        