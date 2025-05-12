import streamlit as st
from pathlib import Path
import os
import duckdb
from pages import home, detailed_overview, gemini
from chart_kpi import (
    vacancies_by_group,
    attributes_per_field,
    chart_top_occupations,
    # field_pie_chart,
    language_pie_chart,
    working_hours, 
    working_duration,
    duration_pie_chart
)


def show_metric(labels, cols, kpis):
    for label, col, kpi in zip(labels, cols, kpis):
        with col:
            st.metric(label=label, value=kpi)


def layout():
    page = {
        "Home": home.home_layout, #
        "Detailed overview": detailed_overview.overview_layout,
        "Ask Gemini": gemini.gemini_layout
    }
    choice = st.sidebar.radio("Välj vy", list(page.keys()))
    page[choice]()
    # st.sidebar.balloons()
    # st.sidebar.
    # home.home_layout()




if __name__ == "__main__":
    working_directory = Path(__file__).parents[2]
    os.chdir(working_directory)
    with duckdb.connect("ads_data.duckdb") as connection:
        df_kultur = connection.execute("SELECT * FROM mart.mart_kultur_media").df()

    layout()
