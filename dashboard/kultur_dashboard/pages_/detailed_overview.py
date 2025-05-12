import streamlit as st
from chart_kpi import (
    attributes_per_field,
    chart_top_occupations,
    # field_pie_chart,
    language_pie_chart,
    working_hours, 
    working_duration,
    duration_pie_chart, 
    show_metric
)



def overview_layout():
    field = 'Kultur, Media, Design'
    st.markdown("# Detailed overview ")
    st.markdown("### Se mest lediga jobb baserat på:"
)  # TODO fixa här också. ta occupation_group och visa occupation/city
    # field = st.selectbox(" Select your group ", fields)
    sort_on = st.selectbox("Sortera på", ["workplace_city", "employer_name"])
    # Finsortera på att välja stad eller välja yrke, och därifrån se hur stor andel av jobb som kräver erfarenhet osv? 

    fig = chart_top_occupations(field, sort_on)
    st.plotly_chart(fig)
    
    # st.plotly_chart(field_pie_chart()) #TODO fixa, inge kul att se alla groups!

    ## Efter sortering på yrkesgrupp, visa hur många jobb som kräver attributes
    st.markdown(f"#### Antal jobb för grupp {field} som kräver:")  # TODO gör i procent? #TODO hitta vad för slags erfarenhet som krävs? 
    labels = ["Erfarenhet", "Körkort", "Tillgång till egen bil"]
    cols = st.columns(3)
    kpis = attributes_per_field(field)
    show_metric(labels, cols, kpis)

    ## Visa hur många jobb som har hel/deltid
    st.markdown(f"#### Antal jobb för {field} som har:")
    hours_type, amount = working_hours()
    labels = hours_type
    cols = st.columns(2)
    kpis = amount
    show_metric(labels, cols, kpis)
    
    duration, vacancies = working_duration()
    labels = duration
    cols = st.columns(6)
    kpis = vacancies
    show_metric(labels, cols, kpis)
    
    st.plotly_chart(duration_pie_chart())
    
    #Pie-chart för languages
    fig, total_languages = language_pie_chart()
    st.markdown(f"### Antal jobb som har ett krav på språk: {total_languages}")  # TODO gör i procent?
    st.plotly_chart(fig)
    
    
if __name__ == "__main__":
    overview_layout()