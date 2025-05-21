import plotly.express as px
import os 
from pathlib import Path
import streamlit as st
import duckdb

working_directory = Path(__file__).parents[2]
os.chdir(working_directory)
with duckdb.connect("ads_data.duckdb") as connection:
    df_kultur = connection.execute("SELECT * FROM mart.mart_kultur_media").df()
df_kultur.columns = df_kultur.columns.str.replace("_", " ").str.title()

#1. totalt antal lediga jobb. # totalt antal städer. 
total_citys = df_kultur["Workplace City"].nunique()
total_vacancies = df_kultur["Vacancies"].sum()
total_employers = df_kultur["Employer Name"].nunique()
# 2.TOP 3: yrkesgrupper med mest lediga jobb. TOP 3 kommuner med mest lediga jobb 
def show_metric(labels, cols, kpis):
    for label, col, kpi in zip(labels, cols, kpis):
        with col:
            st.metric(label=label, value=kpi)
            
def vacancies_by_group():
    occupation_fields = df_kultur.groupby("Occupation")["Vacancies"].sum().sort_values(ascending=False).reset_index()
    fields = occupation_fields["Occupation"]
    vacancies = occupation_fields["Vacancies"]
    
    return fields, vacancies

def attributes_per_field (field): 
    
    # df = df_kultur[df_kultur["occupation_field"] == field]
    df_attributes = df_kultur.groupby("Occupation Field")[["Experience Required", "Driving License", "Access To Own Car"]].sum().reset_index()
    experience = df_attributes["Experience Required"]
    licence = df_attributes["Driving License"]
    car = df_attributes["Access To Own Car"]
    return experience, licence, car 

def working_hours():
    df_hours_type = df_kultur.groupby("Working Hours Type")["Vacancies"].sum().sort_values(ascending=False).reset_index()
    hours_type = df_hours_type["Working Hours Type"]
    vacancies = df_hours_type["Vacancies"]
    return hours_type, vacancies 

def working_duration(): 
    df_duration = df_kultur[df_kultur["Duration"] != 'ej angiven']
    df_duration = df_duration.groupby("Duration")["Vacancies"].sum().sort_values().reset_index()
    duration = df_duration["Duration"]
    vacancies = df_duration["Vacancies"]
    return duration, vacancies

def detailed_metric(detailed_sort):
    # col_list = []
    # for col in df.columns:
    #     col_list.append(col)
    if detailed_sort == 'Must Have Languages': 
        df = df_kultur[df_kultur[detailed_sort] != 'ej specifierat']
    # df = df_kultur
    else: 
        df = df_kultur[df_kultur[detailed_sort] != 'ej angiven']
    
    df = df.groupby(detailed_sort)["Vacancies"].sum().sort_values(ascending=False).reset_index()
    
    labels = df[detailed_sort]
    cols = st.columns(len(df[detailed_sort]))
    kpis = df["Vacancies"]
    return show_metric(labels, cols, kpis)
    
def general_pie_chart(sort_on,get_unique,detailed_sort): #TODO lägg in ej angiven på languages och working_hours_type 

    df = df_kultur[df_kultur[detailed_sort] != 'ej angiven']
    df = df[df[sort_on] == get_unique]
    fig =  px.pie(df.groupby(detailed_sort)["Vacancies"].sum().reset_index(), names=detailed_sort, values="Vacancies", hole=0.2)
    length = df["Vacancies"].sum()
    return fig, length
    
# def vacancies(df, input,field): 
#     return df[df["occupation_field"] == field].groupby(input)["vacancies"].sum().sort_values(ascending=False).reset_index()

def chart_top_occupations(field, sort_on):

    df = df_kultur.groupby(sort_on)["Vacancies"].sum().sort_values(ascending=False).reset_index()
    bar = st.slider("Antal staplar att visa", min_value=10, max_value=20, step=1)

    fig = px.bar(df.head(bar), x=sort_on, y="Vacancies")
    fig.update_layout(title_text=f"Top {bar} {sort_on}s with most vacancies in field: {field}")
    return fig, df

# def language_pie_chart(): #hole=0.3
#     language = df_kultur[df_kultur["Must Have Languages"] != 'ej specifierat']
#     language = language.groupby("Must Have Languages")["vacancies"].sum().reset_index()
#     fig = px.pie(language, names="Must Have Languages", values="vacancies")
#     total_languages = language["vacancies"].sum()
    
#     return fig, total_languages
    

# def field_pie_chart():
#     mart_full_time = df_kultur.groupby("occupation_group")["vacancies"].sum().sort_values(ascending=False).reset_index(name="total vacancies")
#     pie_fig = px.pie(mart_full_time,values="total vacancies",names="occupation_group",width=350, height=350)
#     return pie_fig

# def duration_pie_chart():
#     fig = px.pie(df_kultur.groupby("duration")["vacancies"].sum().sort_values().reset_index(), values="vacancies", names="duration")
#     return fig