import streamlit as st
from pages_ import home, detailed_overview, gemini
import os 
import duckdb
from pathlib import Path
# from pages import file_1

def layout():
    groups = {
        "mart_ads": "mart_ads",
        "mart_installation_drift_underhall": "mart_installation_drift_underhall", #Installation, Drift, Underhåll
        "mart_kultur_media": "mart_kultur_media",
        "mart_kropp_skonhet": "mart_kropp_skonhet"
    }
    group = st.sidebar.radio("Välj yrkesgrupp", list(groups.keys()))
    working_directory = Path(__file__).parents[2]
    os.chdir(working_directory)
    with duckdb.connect("ads_data.duckdb") as connection:
        df = connection.execute(f"SELECT * FROM mart.{group}").df()

    page = {
        "Home": home.home_layout, 
        "Detailed overview": detailed_overview.overview_layout,
        "Ask Gemini": gemini.gemini_layout
    }
    choice = st.sidebar.radio("Välj vy", list(page.keys()))
    
    page[choice](df)
    



if __name__ == "__main__":
    layout()

