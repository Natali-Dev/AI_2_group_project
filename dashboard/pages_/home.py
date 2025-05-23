import streamlit as st
import os
import duckdb
from pathlib import Path
# from chart_kpi import vacancies_by_group, chart_top_occupations, total_employers,show_metric #total_vacancies
from kpi import (
    total_vacancies,
    top_occupations,
    # vacancies_per_city,
    # top_employers,
    # occupations_group_counts,
    # get_attributes_per_field,
)
from chart import (
    bar_chart #, pie_chart, display_data_table, map_chart
)

def home_layout(current_df, field):

    st.title(f"{field}")
    
    st.write(
        f"En Dashboard för att hjälpa rekryterare som jobbar inom {field.lower()} att få en bra översikt över arbetsmarknaden just nu."
    )
    
    st.header("Övergripande statistik")
    col1, col2, col3, col4 = st.columns(4)
    st.write("------------------")

    col1.metric("Totalt antal lediga jobb", total_vacancies(current_df))
    col2.metric("Antal städer", current_df["workplace_city"].nunique())
    col3.metric("Antal arbetsgivare", current_df["employer_name"].nunique())
    col4.metric("Totalt antal annonser", len(current_df))

    # Most requested occupations
    st.header("Mest efterfrågade yrken")
    top_occ = top_occupations(current_df)
    top_occ = top_occ.rename(columns={"occupation": "Yrke", "count": "Antal"})
    st.plotly_chart(bar_chart(top_occ, "Yrke", "Antal", "Mest efterfrågade yrken"))

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
    
# if __name__ == "__main__":

#     home_layout()
