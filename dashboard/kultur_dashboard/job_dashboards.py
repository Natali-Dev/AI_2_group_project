import streamlit as st
from pages_ import home, detailed_overview, gemini
from kropps_skonhetvard_dashboard import dashboard

def layout():
    
    group = st.sidebar.radio("Välj yrkesgrupp", ["Alla","Kultur", "Installation", "Skönhetsvård"])
    if group == "Kultur":
        page = {
            "Home": home.home_layout, 
            "Detailed overview": detailed_overview.overview_layout,
            "Ask Gemini": gemini.gemini_layout
        }
    elif group == "Skönhetsvård":
        page = {
            # "Home": dashboard.layout,
            "Ask Gemini": gemini.gemini_layout
        }
    choice = st.sidebar.radio("Välj vy", list(page.keys()))
    page[choice]()



if __name__ == "__main__":
    layout()

