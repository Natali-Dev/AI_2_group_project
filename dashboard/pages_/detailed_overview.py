import streamlit as st
import os
import duckdb
from pathlib import Path

from kpi import (
    attributes_per_field,
    show_metric,
    occupations_group_counts,
    # total_vacancies,
    # top_occupations,
    # vacancies_per_city,
    # top_employers,
    # get_attributes_per_field,

)
from chart import (
    pie_chart, map_chart, general_pie_chart, chart_top_occupations #bar_chart, display_data_table
)

def overview_layout(current_df, field):
    st.markdown("# Detailed overview")
    

    # Metric som visar hur många jobb som kräver attributes: "Erfarenhet", "Körkort", "Tillgång till egen bil
    st.markdown(f"### Antal jobb för grupp {field.lower()} som kräver:")
    labels = ["Erfarenhet", "Körkort", "Tillgång till egen bil"]
    cols = st.columns(3)
    kpis = attributes_per_field(current_df)
    show_metric(labels, cols, kpis)

    if "occupation_group" in current_df:
        st.header("Fördelning av yrkesgrupper")
        occupations_group_counts_df = occupations_group_counts(current_df)
        occupations_group_counts_df = occupations_group_counts_df.rename(columns={"occupation_group": "Yrkesgrupp", "count": "Antal"})
        
        if not occupations_group_counts_df.empty:
            st.plotly_chart(pie_chart(occupations_group_counts_df, "Yrkesgrupp", "Antal", "Fördelning av yrkesgrupper"))
        else:
            st.warning("Inga yrkesgrupper att visa")
    else:
        st.warning("Ingen data för yrkesgrupper tillgänglig.")

        
        
    # Graf med selectbox och st.slider där man kan välja hur många bars man vill se
    st.markdown("### Se mest lediga jobb baserat på:") 
    sort_on = {"Arbetsort": "workplace_city", "Arbetsgivare": "employer_name", "Yrke": "occupation"}[
    st.selectbox("Sortera på", ["Arbetsort", "Arbetsgivare", "Yrke"])
]

    
    fig, df = chart_top_occupations(current_df, sort_on, field)
    
    cols = st.columns(2)
    
    with cols[0]: # Ruta 1, med barplot
        st.plotly_chart(fig)

    with cols[1]: # Ruta 2, med pie-chart
        sort_options = {
            "Språkkrav": "must_have_languages", 
            "Anställningstyp": "working_hours_type", 
            "Anställningslängd": "duration", 
            "Erfarenhet": "experience_required", 
            "Körkort": "driving_license", 
            "Tillgång till egen bil": "access_to_own_car"
        }
        
        get_unique = st.selectbox("Fortsätt sortera på", df[sort_on].unique()) 
        detailed_sort = sort_options[
            st.selectbox("Se graf med", list(sort_options.keys()))
        ]

        pie_fig, lenght = general_pie_chart(current_df, sort_on, get_unique, detailed_sort)
        st.markdown(f"#### Antal jobb som har lagt in: {lenght}")
        st.plotly_chart(pie_fig)
        
        # Pie-chart som visar fördelning av yrkesgrupper

    # map 
    st.header("Karta över Sverige med lediga jobb")
    st.plotly_chart(map_chart(current_df))
    
