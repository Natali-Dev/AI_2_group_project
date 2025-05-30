import streamlit as st
from pages_ import home, detailed_overview, gemini, gemini_chunks, best_ad_gemini
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

    
    all_pages = {
        "Home": home.home_layout,
        "Detailed overview": detailed_overview.overview_layout,
        "Ask Gemini": gemini.gemini_layout,
        # "Ask Gemini with chunks and plots": gemini_chunks.gemini_chunks_layout,
        "Find the best ad - with Gemini": best_ad_gemini.best_ad_layout
    }

    # Steg 2: Bestäm vilka sidor som ska visas baserat på 'field'
    if field == "Alla jobb":
        # Om "Alla jobb" är valt, filtrera bort Gemini- och Embedding-sidorna
        display_pages = {
            key: value for key, value in all_pages.items()
            if "Gemini" not in key and "Find the best ad" not in key
        }
    else:
        # Annars, visa alla sidor
        display_pages = all_pages


    choice_view = st.sidebar.radio("Välj vy", list(display_pages.keys()))

   
    if choice_view in display_pages:
        display_pages[choice_view](df, field)
    else:
        
        home.home_layout(df, field)
        st.sidebar.warning(f"Vyn '{choice_view}' är inte tillgänglig för 'Alla jobb'. Visar 'Home' istället.")

    

if __name__ == "__main__":
    layout()