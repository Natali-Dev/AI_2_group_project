import streamlit as st
from chart_kpi import vacancies_by_group, chart_top_occupations
from kultur_dashboard import show_metric
import duckdb
import os
from pathlib import Path
working_directory = Path(__file__).parents[3]
os.chdir(working_directory)
with duckdb.connect("ads_data.duckdb") as connection:
    df_kultur = connection.execute("SELECT * FROM mart.mart_kultur_media").df()
def home_layout():
    field = 'Kultur, Media, Design'
    total_citys = df_kultur["workplace_city"].nunique()
    total_vacancies = df_kultur["vacancies"].sum()
    st.markdown("# Job Ads Dashboard - Kultur, Media, Design")
    # Total layout for sweden:
    st.write(
        "En Dashboard för att hjälpa rekryterare som jobbar inom Kultur, Media och Design att få en bra översikt över arbetsmarknaden just nu."
    )
    labels = ["Totalt antal lediga jobb", "Totalt antal städer"]
    cols = st.columns(2)
    kpis = round(total_vacancies), total_citys
    show_metric(labels, cols, kpis)
    
    fig2 = chart_top_occupations(field, "occupation")
    st.plotly_chart(fig2)
    # st.write("--------------------------------------")

    st.markdown("### Top 5 yrkesgrupper med flest lediga jobb:")
    fields, vacanices = vacancies_by_group()
    labels = fields
    cols = st.columns(5)
    kpis = vacanices
    show_metric(labels, cols, kpis)
    # st.markdown("### Topplista på yrken: ")
    
if __name__ == "__main__":
    working_directory = Path(__file__).parents[3]
    os.chdir(working_directory)
    with duckdb.connect("ads_data.duckdb") as connection:
        df_kultur = connection.execute("SELECT * FROM mart.mart_kultur_media").df()
    home_layout()