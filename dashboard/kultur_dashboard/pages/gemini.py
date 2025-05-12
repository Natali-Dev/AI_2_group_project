import streamlit as st
from chart_kpi import vacancies_by_group, chart_top_occupations
from kultur_dashboard import show_metric
import duckdb
import os
from pathlib import Path

def gemini_layout():
    st.markdown("## Ställ en fråga till Gemini")
    st.write("Vilka top 10 erfarenheter och krav har top {1} {företags_namn}/{stad}")
    st.selectbox("Välj en fråga", ["Hej"])
    # utgå ifrån vilken field som är vald