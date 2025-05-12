import plotly.express as px
import os 
from pathlib import Path
import streamlit as st
import duckdb

working_directory = Path(__file__).parents[2]
os.chdir(working_directory)
with duckdb.connect("ads_data.duckdb") as connection:
    df_kultur = connection.execute("SELECT * FROM mart.mart_kultur_media").df()

#1. totalt antal lediga jobb. # totalt antal städer. 
total_citys = df_kultur["workplace_city"].nunique()
total_vacancies = df_kultur["vacancies"].sum()
# 2.TOP 3: yrkesgrupper med mest lediga jobb. TOP 3 kommuner med mest lediga jobb 
def show_metric(labels, cols, kpis):
    for label, col, kpi in zip(labels, cols, kpis):
        with col:
            st.metric(label=label, value=kpi)
            
def vacancies_by_group():
    occupation_fields = df_kultur.groupby("occupation_group")["vacancies"].sum().sort_values(ascending=False).reset_index()
    fields = occupation_fields["occupation_group"]
    vacancies = occupation_fields["vacancies"]
    
    return fields, vacancies

def attributes_per_field (field): 
    
    # df = df_kultur[df_kultur["occupation_field"] == field]
    df_attributes = df_kultur.groupby("occupation_field")[["experience_required", "driving_license", "access_to_own_car"]].sum().reset_index()
    experience = df_attributes["experience_required"]
    licence = df_attributes["driving_license"]
    car = df_attributes["access_to_own_car"]
    return experience, licence, car 

def working_hours():
    df_hours_type = df_kultur.groupby("working_hours_type")["vacancies"].sum().sort_values(ascending=False).reset_index()
    hours_type = df_hours_type["working_hours_type"]
    vacancies = df_hours_type["vacancies"]
    return hours_type, vacancies 

def working_duration(): 
    df_duration = df_kultur.groupby("duration")["vacancies"].sum().sort_values().reset_index()
    duration = df_duration["duration"]
    vacancies = df_duration["vacancies"]
    return duration, vacancies
# def vacancies(df, input,field): 
#     return df[df["occupation_field"] == field].groupby(input)["vacancies"].sum().sort_values(ascending=False).reset_index()

def chart_top_occupations(field, sort_on):

    df = df_kultur.groupby(sort_on)["vacancies"].sum().sort_values(ascending=False).reset_index().head(10)
        
    fig = px.bar(df.head(10), x=sort_on, y="vacancies")
    fig.update_layout(title_text=f"Top 10 {sort_on}s with most vacancies in field: {field}")
    return fig

def language_pie_chart():
    language = df_kultur[df_kultur["must_have_languages"] != 'ej specifierat']
    language = language.groupby("must_have_languages")["vacancies"].sum().reset_index()
    fig = px.pie(language, names="must_have_languages", values="vacancies")
    total_languages = language["vacancies"].sum()
    
    return fig, total_languages
    
def field_pie_chart():
    mart_full_time = df_kultur.groupby("occupation_group")["vacancies"].sum().sort_values(ascending=False).reset_index(name="total vacancies")
    pie_fig = px.pie(mart_full_time,values="total vacancies",names="occupation_group",width=350, height=350)
    return pie_fig

def duration_pie_chart():
    fig = px.pie(df_kultur.groupby("duration")["vacancies"].sum().sort_values().reset_index(), values="vacancies", names="duration")
    return fig