import streamlit as st
from pages_ import home, detailed_overview, gemini

def layout():
    
    st.sidebar.radio("Välj yrkesgrupp", ["Alla","Kultur", "Installation", "Skönhetsvård"])
    page = {
        "Home": home.home_layout, 
        "Detailed overview": detailed_overview.overview_layout,
        "Ask Gemini": gemini.gemini_layout
    }
    choice = st.sidebar.radio("Välj vy", list(page.keys()))
    page[choice]()



if __name__ == "__main__":
    layout()

