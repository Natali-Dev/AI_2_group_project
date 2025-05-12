import streamlit as st
from chart_kpi import vacancies_by_group, chart_top_occupations
# from kultur_dashboard import show_metric
import duckdb
import os
from pathlib import Path

from google import genai
import os
from dotenv import load_dotenv
import duckdb
# from kultur_dashboard import df_kultur

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def gemini_layout():
    st.markdown("## Ställ en fråga till Gemini")
    st.write("Vilka top 10 erfarenheter och krav har top {1} {företags_namn}/{stad}")
    st.selectbox("Välj en fråga", ["Hej"])
    # utgå ifrån vilken field som är vald
    
# if __name__ == "__main__": 
#     pass