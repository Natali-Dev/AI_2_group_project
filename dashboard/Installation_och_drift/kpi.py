from pathlib import Path
import pandas as pd
import os 
import duckdb


working_directory = Path(__file__).parents[2]
os.chdir(working_directory)
with duckdb.connect("ads_data.duckdb") as connection:
    df_mart = connection.execute("SELECT * FROM mart.mart_installation_drift_underhall").df()


# Count total number of vacancies
def total_vacancies(df: pd.DataFrame):
        return df["vacancies"].sum()
    
# most common occupations in the field
def top_occupations(df: pd.DataFrame, n: int = 10):
        return df["occupation"].value_counts().head(n).reset_index()
    
# count total number of jobs per city
def vacancies_per_city (df: pd.DataFrame):
        return (
            df.groupby("workplace_city")["vacancies"]
            .sum().reset_index()
            .rename(columns={"workplace_city": "Stad", "vacancies": "Antal jobb"})
        )
    
# pick out the biggest employers in the field
def top_employers(df: pd.DataFrame):
        return df["employer_name"].value_counts().head(5).reset_index()
    
# jobs per field
def occupations_group_counts(df: pd.DataFrame):
        return df.groupby("occupation_group").size().reset_index(name="Antal")
    

# get information about the attributes required for a job
def get_attributes_per_field(df: pd.DataFrame):
    s = df[["experience_required", "driving_license", "access_to_own_car"]].sum()
    s.index = ["Erfarenhet", "Körkort", "Tillgång till egen bil"]
    return s.reset_index(name="Antal jobb").rename(columns={"index": "Egenskap"})

        
        