import streamlit as st
from chart_kpi import (
    attributes_per_field,
    chart_top_occupations,
    # field_pie_chart,
    # language_pie_chart,
    working_hours, 
    working_duration,
    # duration_pie_chart, 
    general_pie_chart,
    detailed_metric,
    show_metric,
)



def overview_layout():
    field = 'Kultur, Media, Design'
    st.markdown("# Detailed overview ")
    
    # st.plotly_chart(field_pie_chart()) #TODO fixa, inge kul att se alla groups!

    ## Efter sortering på yrkesgrupp, visa hur många jobb som kräver attributes
    st.markdown(f"### Antal jobb för grupp {field} som kräver:")  # TODO gör i procent? #TODO hitta vad för slags erfarenhet som krävs? 
    labels = ["Erfarenhet", "Körkort", "Tillgång till egen bil"]
    cols = st.columns(3)
    kpis = attributes_per_field(field)
    show_metric(labels, cols, kpis)

    # Visa hur många jobb som har hel/deltid
    st.markdown(f"### Antal jobb för {field} som har:")
    st.markdown("##### Anställningstyp")
    hours_type, amount = working_hours()
    labels = hours_type
    cols = st.columns(2)
    kpis = amount
    show_metric(labels, cols, kpis)
    st.markdown("##### Anställningslängd") #TODO dela upp i 3 kolumner
    duration, vacancies = working_duration()
    labels = duration
    cols = st.columns(5)
    kpis = vacancies
    show_metric(labels, cols, kpis)

    st.markdown("### Se mest lediga jobb baserat på:")
    sort_on = st.selectbox("Sortera på", ["Workplace City", "Employer Name", "Occupation"])
    # df = df.groupby(sort_on)
    fig, df = chart_top_occupations(field, sort_on)
    # st.write(df)
    cols = st.columns(2)
    with cols[0]:
        # TODO fixa här också. ta occupation_group och visa occupation/city
        # field = st.selectbox(" Select your group ", fields)
        # Finsortera på att välja stad eller välja yrke, och därifrån se hur stor andel av jobb som kräver erfarenhet osv? 

        st.plotly_chart(fig)
    with cols[1]:
        get_unique = st.selectbox("Sortera på", df[sort_on].unique())
        detailed_sort = st.selectbox("Se graf med ", ["Must Have Languages", "Duration", "Working Hours Type"])
        # df = detailed_metric(detailed_sort)
        # st.write(df)
        # df.
        pie_fig, lenght = general_pie_chart(sort_on,get_unique, detailed_sort)
        st.markdown(f"### Antal jobb som har en lagt in: {lenght}")
        st.plotly_chart(pie_fig)
    # st.plotly_chart(duration_pie_chart())
    #Pie-chart för languages
    # fig, total_languages = language_pie_chart()
    # st.plotly_chart(fig)
    
    
if __name__ == "__main__":
    overview_layout()