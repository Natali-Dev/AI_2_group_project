import streamlit as st
from chart_kpi import vacancies_by_group, chart_top_occupations, total_citys, total_vacancies, show_metric

def home_layout():
    field = 'Kultur, Media, Design'

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

    st.markdown("### Top 5 yrkesgrupper med flest lediga jobb:")
    fields, vacanices = vacancies_by_group()
    labels = fields
    cols = st.columns(5)
    kpis = vacanices
    show_metric(labels, cols, kpis)
    # st.markdown("### Topplista på yrken: ")
    
if __name__ == "__main__":

    home_layout()