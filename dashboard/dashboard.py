import streamlit as st
from pathlib import Path
import os
import duckdb

# Hjälp rekryterare som jobbar med de specifika occupation_fields genom att skapa en dashboard.
## Metrics:
# 1. totalt antal lediga jobb. 2 totalt antal städer. #3. TOP 3: yrken med mest lediga jobb. 4. TOP 3 regioner med mest lediga jobb  något mer?
# vilket yrke har högst andel lediga jobb? linjediagram med en linje per yrke
# vilken stad har högst andel lediga jobb? linjediagram med en linje per yrke

## Sålla per yrkesgrupp (occ_field eller df:arna):
# vilken arbetsgivare har högst andel lediga jobb? barchart
# vilken yrkesgrupp har högst andel lediga jobb? occ_group      barchart
# andel jobb som kräver körkort + egen bil + erfarenhet

# # avancerat: hur lång är application_deadline i snitt? Vilken stad har störst variation av yrken? Vilka kommuner erbjuder heltid oftast?
# # diagram för region så det är sveriges karta
from kpi import (
    top_occupations,
    vacancies_by_group,
    attributes_per_field,
    # top_municipalitys,
)
from chart import chart_top_occupations, pie_chart


def show_metric(labels, cols, kpis):
    for label, col, kpi in zip(labels, cols, kpis):
        with col:
            st.metric(label=label, value=kpi)


def layout():
    total_citys = df_mart["workplace_city"].nunique()
    total_vacancies = df_mart["vacancies"].sum()
    st.markdown("# Job Ads Dashboard")
    # Total layout for sweden:
    st.write(
        "En Dashboard för att hjälpa rekryterare som jobbar med specifika yrkesgrupper att få en bra översikt över arbetsmarknaden just nu."
    )

    labels = ["Totalt antal lediga jobb", "Totalt antal städer"]
    cols = st.columns(2)
    kpis = round(total_vacancies), total_citys
    show_metric(labels, cols, kpis)

    st.markdown("### Lediga jobb i:")
    labels = top_occupations()
    cols = st.columns(3)
    kpis = vacancies_by_group()
    show_metric(labels, cols, kpis)

    st.plotly_chart(pie_chart())

    st.markdown("### Finsortera på yrkesgrupp och kommun/yrke:")
    field = st.selectbox(" Select your field ", top_occupations())
    sort_on = st.selectbox("Sort on", ["workplace_city", "occupation"])

    fig = chart_top_occupations(field, sort_on)
    st.plotly_chart(fig)
    ## Efter sortering på yrkesgrupp, visa hur många jobb som kräver attributes
    st.markdown(f"### Antal jobb för grupp {field} som kräver:")  # TODO gör i procent?
    labels = ["Erfarenhet", "Körkort", "Tillgång till egen bil"]
    cols = st.columns(3)
    kpis = attributes_per_field(field)
    show_metric(labels, cols, kpis)

    st.markdown("## Ställ en fråga till Gemini")
    st.selectbox("Välj en fråga", ["Hej"])
    # utgå ifrån vilken field som är vald



if __name__ == "__main__":
    working_directory = Path(__file__).parents[1]
    os.chdir(working_directory)
    with duckdb.connect("ads_data.duckdb") as connection:
        df_mart = connection.execute("SELECT * FROM mart.mart_ads").df()

    layout()
    
    # TODO job_ads__nice_to_have__languages ta med denna! så kan man se
    # city_1, city_2, city_3, city_4, city_5, vac_1, vac_2, vac_3, vac_4, vac_5 = (
    #     top_municipalitys()
    # )

    # labels = [city_1, city_2, city_3, city_4, city_5]
    # kpis = [vac_1, vac_2, vac_3, vac_4, vac_5]  # jobb per kommun
    # cols = st.columns(5)
    # for label, col, kpi in zip(labels, cols, kpis):
    #     with col:
    #         st.metric(label=label, value=kpi)

    # city = "workplace_municipality"
    # occupation = "occupation"
    # df_test = vacancies(df_technical, city)
    # x_input = st.selectbox("Select x value", ["workplace_municipality", "city"])
    # y_input = st.selectbox("Select y value", ["vacancies"])
    # fig1 = px.bar(df_ads, x=x_input, y=y_input)
    # st.plotly_chart(fig1)
