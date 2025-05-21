import streamlit as st
from pathlib import Path
import os
import duckdb
import pandas as pd
from kpi import (
    total_vacancies,
    top_occupations,
    vacancies_per_city,
    top_employers,
    occupations_group_counts,
    get_attributes_per_field,
)
from chart import (
    bar_chart, pie_chart, display_data_table, map_chart
)
def layout(df_kropp_skonhetsvard):

    st.title("Kropp och Skönhet Dashboard")
    
    
    st.header("Övergripande statistik")
    col1, col2, col3 = st.columns(3)
    col1.metric("Totalt antal lediga jobb", total_vacancies(df_kropp_skonhetsvard))
    col2.metric("Antal städer", df_kropp_skonhetsvard["workplace_city"].nunique())
    col3.metric("Antal arbetsgivare", df_kropp_skonhetsvard["employer_name"].nunique())

    # Most requested occupations
    st.header("Mest efterfrågade yrken")
    top_occ = top_occupations(df_kropp_skonhetsvard)
    top_occ = top_occ.rename(columns={"occupation": "Yrke", "count": "Antal"})
    st.plotly_chart(bar_chart(top_occ, "Yrke", "Antal", "Mest efterfrågade yrken"))

    # Available jobs per city
    st.header("Lediga jobb per stad")
    city_vacancies = vacancies_per_city(df_kropp_skonhetsvard)
    st.plotly_chart(bar_chart(city_vacancies, "Stad", "Antal jobb", "Lediga jobb per stad"))

    # Pie chart for occupational groups

    if "occupation_group" in df_kropp_skonhetsvard:
        st.header("Fördelning av yrkesgrupper")
        occupations_group_counts_df = occupations_group_counts(df_kropp_skonhetsvard)
        occupations_group_counts_df = occupations_group_counts_df.rename(columns={"occupation_group": "Yrkesgrupp", "count": "Antal"})
        if not occupations_group_counts_df.empty:
            st.plotly_chart(pie_chart(occupations_group_counts_df, "Yrkesgrupp", "Antal", "Fördelning av yrkesgrupper"))
        else:
            st.warning("Inga yrkesgrupper att visa")
        
    else:
        st.warning("Ingen data för yrkesgrupper tillgänglig.")

    #map 
    st.header("Karta över Sverige med lediga jobb")
    st.plotly_chart(map_chart(df_kropp_skonhetsvard))

    # Attributes required for jobs
    st.header("Krav för anställning")
    attributes_df = get_attributes_per_field(df_kropp_skonhetsvard)
    display_data_table(attributes_df, "Krav för anställning")
    
if __name__ == "__main__":
    working_directory = Path(__file__).parents[2]
    os.chdir(working_directory)
    try:
        with duckdb.connect("ads_data.duckdb") as connection:
            df_kropp_skonhetsvard = connection.execute("SELECT * FROM mart.mart_kropp_skonhet").df()
    except Exception as e:
        st.error(f"Failed to load data from DuckDB: {e}")
        st.stop()  
    layout(df_kropp_skonhetsvard)