import streamlit as st
import os
import duckdb
from pathlib import Path
from chart_kpi import vacancies_by_group, chart_top_occupations, total_citys, total_employers,show_metric, total_vacancies
from kpi import (
    # total_vacancies,
    top_occupations,
    vacancies_per_city,
    top_employers,
    occupations_group_counts,
    get_attributes_per_field,
)
from chart import (
    bar_chart, pie_chart, display_data_table, map_chart
)
working_directory = Path(__file__).parents[3]
os.chdir(working_directory)
with duckdb.connect("ads_data.duckdb") as connection:
    df_kropp_skonhetsvard = connection.execute("SELECT * FROM mart.mart_kropp_skonhet").df()
def home_layout():
    st.title("Kropp och Skönhet Dashboard")
    # st.markdown("# Job Ads Dashboard - Kultur, Media, Design")
    
    st.write(
        "En Dashboard för att hjälpa rekryterare som jobbar inom Kultur, Media och Design att få en bra översikt över arbetsmarknaden just nu."
    )
    
    st.header("Övergripande statistik")
    # col1, col2, col3 = st.columns(3)
    st.write("------------------")
    labels = ["Totalt antal lediga jobb", "Totalt antal städer", "Totalt antal arbetsgivare"] 
    cols = st.columns(3)
    kpis = round(total_vacancies), total_citys, total_employers
    show_metric(labels, cols, kpis)
    # col1.metric("Totalt antal lediga jobb", total_vacancies(df_kropp_skonhetsvard))
    # col2.metric("Antal städer", df_kropp_skonhetsvard["workplace_city"].nunique())
    # col3.metric("Antal arbetsgivare", df_kropp_skonhetsvard["employer_name"].nunique())

    # Most requested occupations
    # st.header("Mest efterfrågade yrken")
    top_occ = top_occupations(df_kropp_skonhetsvard)
    top_occ = top_occ.rename(columns={"occupation": "Yrke", "count": "Antal"})
    st.plotly_chart(bar_chart(top_occ, "Yrke", "Antal", "Mest efterfrågade yrken"))
    field = 'Kultur, Media, Design'

    # Total layout for sweden:

    # st.markdown("### Top 5 yrken med flest lediga jobb:")
    # fields, vacanices = vacancies_by_group()
    # labels = fields
    # cols = st.columns(5)
    # kpis = vacanices
    # show_metric(labels, cols, kpis)
    
    # fig2, df = chart_top_occupations(field, "Occupation Group")
    # st.plotly_chart(fig2)

    # st.markdown("### Topplista på yrken: ")
    
if __name__ == "__main__":

    home_layout()
