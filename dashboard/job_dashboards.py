import streamlit as st
from pages_ import home, detailed_overview, gemini, gemini_chunks, embedding
import os 
import duckdb
from pathlib import Path

def layout():
    groups = {
        "Alla jobb": "mart_ads",
        "Installation, Drift, Underhåll": "mart_installation_drift_underhall",
        "Kultur, Media, Design": "mart_kultur_media",
        "Kropp och skönhetsvård": "mart_kropp_skonhet"
    }
    field = st.sidebar.radio("Välj yrkesgrupp", list(groups.keys()))
    group = groups[field] #group = "Alla[mart_ads]"
    
    working_directory = Path(__file__).parents[1] # Hämta ut DF
    os.chdir(working_directory)
    with duckdb.connect("ads_data.duckdb") as connection:
        df = connection.execute(f"SELECT * FROM mart.{group}").df()

    page = {
        "Home": home.home_layout, 
        "Detailed overview": detailed_overview.overview_layout,
        "Ask Gemini": gemini.gemini_layout,
        "Ask Gemini with chunks and plots": gemini_chunks.gemini_chunks_layout,
        "Find the best ad - with embedding": embedding.embedding_layout
    }
    choice_view = st.sidebar.radio("Välj vy", list(page.keys()))
    
    page[choice_view](df, field) 
    

if __name__ == "__main__":
    layout()

