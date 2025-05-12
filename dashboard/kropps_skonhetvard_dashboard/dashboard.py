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
    bar_chart, pie_chart, display_text, map_chart
)

def layout():
    st.title("Kropp och Skönhet Dashboard")

    st.header("Övergripande statistik")
    col1, col2, col4 = st.columns(3)
    
