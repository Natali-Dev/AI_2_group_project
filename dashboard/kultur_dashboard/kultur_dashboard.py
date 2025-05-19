import streamlit as st
from pathlib import Path
import os
import duckdb

def show_metric(labels, cols, kpis):
    for label, col, kpi in zip(labels, cols, kpis):
        with col:
            st.metric(label=label, value=kpi)

def layout():
    occupation_fields = df_kultur.groupby("occupation_field")["vacancies"].sum().sort_values(ascending=False).reset_index().head(5)
    occ_1 = occupation_fields["vacancies"]


    st.markdown("### Lediga jobb i:")
    labels = ["1","2","3"]
    cols = st.columns(3)
    kpis = occ_1
    show_metric(labels, cols, kpis)


if __name__ == "__main__":
    working_directory = Path(__file__).parents[1]
    os.chdir(working_directory)
    with duckdb.connect("ads_data.duckdb") as connection:
        df_kultur = connection.execute("SELECT * FROM mart.mart_kultur_media").df()

    layout()
    