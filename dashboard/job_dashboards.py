import streamlit as st
import pandas as pd # Importera pandas här om det inte redan görs i load_data
import duckdb
import os
import sys # Importera sys för sys.path justering
from pathlib import Path

# Lägg till projektets rotkatalog i sys.path för att kunna importera från 'definitions'
# Detta antar att job_dashboards.py ligger i en undermapp (t.ex. 'dashboard')
# till projektets rotkatalog (t.ex. 'AI_2_group_project')
try:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
        print(f"INFO (job_dashboards.py): Lade till {PROJECT_ROOT} i sys.path")
    from definitions import DB_PATH # Importera DB_PATH från definitions.py
except ImportError:
    st.error("VIKTIGT: Kunde inte importera DB_PATH från definitions.py! Kontrollera att definitions.py finns i projektets rotkatalog och att sökvägen är korrekt.")
    # Fallback om importen misslyckas - detta bör inte hända om allt är rätt konfigurerat
    DB_PATH = "ads_data.duckdb" 
    st.warning(f"Använder fallback DB_PATH: {DB_PATH}. Detta kan leda till fel om filen inte hittas i den förväntade mappen.")

# Importera dina sidmoduler
# Se till att dashboard/pages_/__init__.py existerar för att detta ska fungera
try:
    from pages_ import home, detailed_overview, gemini, gemini_chunks, embedding
except ImportError as e:
    st.error(f"Fel vid import av sidmoduler från 'pages_': {e}")
    st.error("Kontrollera att mappen 'dashboard/pages_' innehåller en __init__.py-fil och alla nödvändiga sidfiler (home.py, gemini.py etc.).")
    # Stoppa appen om sidorna inte kan laddas, då inget kommer fungera
    st.stop()


# Sätt sidkonfigurationen som det första Streamlit-kommandot
st.set_page_config(layout="wide", page_title="Jobb Datanördarna", page_icon="🤖")


@st.cache_data # Cachea datan för bättre prestanda
def load_data_from_db(table_suffix: str):
    """ Laddar data från en specifik mart-tabell i ads_data.duckdb. """
    print(f"INFO (job_dashboards.py): Försöker ladda data från mart.{table_suffix} i databasen: {DB_PATH}")
    if not DB_PATH or not os.path.exists(DB_PATH):
        st.error(f"Databasfilen '{DB_PATH}' hittades inte. Kontrollera sökvägen i definitions.py och att din dbt/dlt pipeline har körts.")
        return pd.DataFrame() 

    try:
        con = duckdb.connect(database=DB_PATH, read_only=True)
        # Bygg queryn säkert med f-sträng för tabellnamnet (som kommer från en kontrollerad dictionary)
        query = f"SELECT * FROM mart.\"{table_suffix}\";" 
        df = con.execute(query).fetchdf()
        con.close()
        print(f"INFO (job_dashboards.py): Laddade {len(df)} rader från mart.{table_suffix}.")
        if df.empty and table_suffix != "mart_ads": # mart_ads kan vara stor, men specifika vyer bör ha data
             st.warning(f"Ingen data returnerades från mart.{table_suffix}. Kontrollera att tabellen är populärad och att yrkesområdet har jobbannonser.")
        return df
    except Exception as e:
        st.error(f"Kunde inte ladda data från mart.{table_suffix} i databasen '{DB_PATH}': {e}")
        return pd.DataFrame()

def layout():
    # Använd en logotyp om du har en, annars kan du ta bort denna rad
    try:
        # Försök hitta bilden relativt till denna filens mapp, sedan en nivå upp, sedan i 'img'
        logo_path = Path(__file__).parent / "img" / "logo.png" 
        if logo_path.exists():
            st.sidebar.image(str(logo_path))
        else:
            st.sidebar.markdown("*(Logotyp saknas)*") # Eller inget alls
    except Exception as e:
        print(f"Kunde inte ladda logotyp: {e}")


    groups = {
        "Alla jobb": "mart_ads", # Tabellen som (antagligen) innehåller alla jobb
        "Installation, Drift, Underhåll": "mart_installation_drift_underhall",
        "Kultur, Media, Design": "mart_kultur_media",
        "Kropp och skönhetsvård": "mart_kropp_skonhet"
        # Lägg till fler här om du har fler mart-tabeller per yrkesområde
    }
    
    # 'selected_occupation_display_name' är det användarvänliga namnet från radio-knappen
    selected_occupation_display_name = st.sidebar.radio("Välj yrkesområde att visa:", list(groups.keys()))
    # 'selected_mart_table_suffix' är suffixet för tabellnamnet i databasen
    selected_mart_table_suffix = groups[selected_occupation_display_name]
    
    # Ladda data för det valda yrkesområdet
    # Denna df kommer att användas av sidor som Home och Detailed Overview
    df_for_view = load_data_from_db(selected_mart_table_suffix)

    st.sidebar.markdown("---")

    page_functions = {
        "Översikt (Hem)": home.home_layout, 
        "Detaljerad Översikt": detailed_overview.overview_layout,
        "Fråga JobbAgenten (AI)": gemini.job_agent_dashboard, # Antager att detta är det korrekta namnet
        # "Ask Gemini with chunks and plots": gemini_chunks.gemini_chunks_layout, # Kommentera in om du använder denna
        # "Find the best ad - with embedding": embedding.embedding_layout # Kommentera in om du använder denna
    }
    
    # Se till att alla sidfunktioner i page_functions är definierade att kunna ta emot (df, field_name)
    # även om de inte använder dem.
    # gemini.job_agent_dashboard(df=None, field=None) är redan fixad för detta.

    selected_view_name = st.sidebar.radio("Välj vy i dashboarden:", list(page_functions.keys()))
    
    # Anropa den valda sidfunktionen
    # Skicka med den specifika DataFrame (df_for_view) och det valda yrkesområdets visningsnamn
    page_functions[selected_view_name](df_for_view, selected_occupation_display_name) 
    

if __name__ == "__main__":
    layout()