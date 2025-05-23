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
    sort_on = st.selectbox("Sortera på", ["workplace_city", "employer_name", "occupation"])
    
    fig, df = chart_top_occupations(current_df, sort_on, field)
    
    cols = st.columns(2)
    
    with cols[0]: # Ruta 1, med barplot
        st.plotly_chart(fig)

    with cols[1]: # Ruta 2, med pie-chart
        get_unique = st.selectbox("Fortsätt sortera på", df[sort_on].unique()) 
        detailed_sort = st.selectbox("Se graf med ", ["must_have_languages", "duration", "working_hours_type", "experience_required", "driving_license", "access_to_own_car"]) 

        pie_fig, lenght = general_pie_chart(current_df,sort_on,get_unique, detailed_sort)
        st.markdown(f"#### Antal jobb som har lagt in: {lenght}")
        st.plotly_chart(pie_fig)
        
        # Pie-chart som visar fördelning av yrkesgrupper

    # map 
    st.header("Karta över Sverige med lediga jobb")
    st.plotly_chart(map_chart(current_df))
    
# if __name__ == "__main__":

#     overview_layout()
    
    
    
    # Visa hur många jobb som har hel/deltid
    # st.markdown(f"### Antal jobb för {field} som har:")
    # st.markdown("##### Anställningstyp")
    # hours_type, amount = working_hours()
    # labels = hours_type
    # cols = st.columns(2)
    # kpis = amount
    # show_metric(labels, cols, kpis)
    # st.markdown("##### Anställningslängd") #TODO dela upp i 3 kolumner
    # duration, vacancies = working_duration()
    # labels = duration
    # cols = st.columns(5)
    # kpis = vacancies
    # show_metric(labels, cols, kpis)
    
    
    # st.plotly_chart(duration_pie_chart())
    #Pie-chart för languages
    # fig, total_languages = language_pie_chart()
    # st.plotly_chart(fig)
    
    # st.title("Kropp och Skönhet Dashboard")
    
    
    # st.header("Övergripande statistik")
    # col1, col2, col3 = st.columns(3)
    # col1.metric("Totalt antal lediga jobb", total_vacancies(df_kropp_skonhetsvard))
    # col2.metric("Antal städer", df_kropp_skonhetsvard["workplace_city"].nunique())
    # col3.metric("Antal arbetsgivare", df_kropp_skonhetsvard["employer_name"].nunique())

    # # Most requested occupations
    # st.header("Mest efterfrågade yrken")
    # top_occ = top_occupations(df_kropp_skonhetsvard)
    # top_occ = top_occ.rename(columns={"occupation": "Yrke", "count": "Antal"})
    # st.plotly_chart(bar_chart(top_occ, "Yrke", "Antal", "Mest efterfrågade yrken"))

    # # Available jobs per city
    # st.header("Lediga jobb per stad")
    # city_vacancies = vacancies_per_city(df_kropp_skonhetsvard)
    # st.plotly_chart(bar_chart(city_vacancies, "Stad", "Antal jobb", "Lediga jobb per stad"))

    # Pie chart for occupational groups
