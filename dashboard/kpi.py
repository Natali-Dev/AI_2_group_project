import duckdb
import os 
from pathlib import Path
# from dash import df_mart, df_total_vacancies

working_directory = Path(__file__).parents[1]
os.chdir(working_directory)
with duckdb.connect("ads_data.duckdb") as connection:
    df_mart = connection.execute("SELECT * FROM mart.mart_ads").df()
#1. totalt antal lediga jobb. # totalt antal städer. 

# 2.TOP 3: yrkesgrupper med mest lediga jobb. TOP 3 kommuner med mest lediga jobb 

def vacancies_by_field():
    occupation_fields = df_mart.groupby("occupation_field")["vacancies"].sum().sort_values(ascending=False).reset_index()
    fields = occupation_fields["occupation_field"]
    vacancies = occupation_fields["vacancies"]
    
    return fields, vacancies

def attributes_per_field (field): 
    # if field == "Alla": 
    #     df_attributes = df_mart[["experience_required", "driving_license", "access_to_own_car"]].sum()
    #     experience = df_attributes["experience_required"]
    #     licence = df_attributes["driving_license"]
    #     car = df_attributes["access_to_own_car"]
    # else:
    df = df_mart[df_mart["occupation_field"] == field]
    df_attributes = df.groupby("occupation_field")[["experience_required", "driving_license", "access_to_own_car"]].sum().reset_index()
    experience = df_attributes["experience_required"]
    licence = df_attributes["driving_license"]
    car = df_attributes["access_to_own_car"]
    
    return experience, licence, car
