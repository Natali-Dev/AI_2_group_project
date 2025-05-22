import plotly.express as px
import os 
from pathlib import Path
import streamlit as st
import duckdb


# metod för att förkenkla att göra metrics
def show_metric(labels, cols, kpis):
    for label, col, kpi in zip(labels, cols, kpis):
        with col:
            st.metric(label=label, value=kpi)
            
# Detailed_overview: KPI till metric för att få ut experience_required, driving_license, access_to_own_car
def attributes_per_field (current_df): 
    experience = current_df["experience_required"].sum()
    licence = current_df["driving_license"].sum()
    car = current_df["access_to_own_car"].sum()

    return experience, licence, car 

# Detailed_overview: Metod för att få ut barplot, används i kolumn 1, workplace city, employer name, occupation
def chart_top_occupations(current_df, sort_on):

    df = current_df.groupby(sort_on)["vacancies"].sum().sort_values(ascending=False).reset_index()
    bar = st.slider("Antal staplar att visa", min_value=10, max_value=20, step=1)

    fig = px.bar(df.head(bar), x=sort_on, y="vacancies")
    fig.update_layout(title_text=f"Top {bar} {sort_on}s with most vacancies in field: field")
    return fig, df

#Detaied_overview: Metod för att få ut pie-chart, används i kolumn 2, languages, duration, working hours type
def general_pie_chart(current_df, sort_on,get_unique,detailed_sort):

    df = current_df[current_df[detailed_sort] != 'ej angiven']
    df = df[df[sort_on] == get_unique]
    fig =  px.pie(df.groupby(detailed_sort)["vacancies"].sum().reset_index(), names=detailed_sort, values="vacancies", hole=0.2)
    length = df["vacancies"].sum()
    return fig, length


###### Gamla plots och KPI som inte används just nu ######

# def vacancies_by_group(current_df):
#     occupation_fields = current_df.groupby("Occupation")["Vacancies"].sum().sort_values(ascending=False).reset_index()
#     fields = occupation_fields["Occupation"]
#     vacancies = occupation_fields["Vacancies"]
    
#     return fields, vacancies


# def working_hours():
#     df_hours_type = current_df.groupby("Working Hours Type")["Vacancies"].sum().sort_values(ascending=False).reset_index()
#     hours_type = df_hours_type["Working Hours Type"]
#     vacancies = df_hours_type["Vacancies"]
#     return hours_type, vacancies 

# def working_duration(): 
#     df_duration = current_df[current_df["Duration"] != 'ej angiven']
#     df_duration = df_duration.groupby("Duration")["Vacancies"].sum().sort_values().reset_index()
#     duration = df_duration["Duration"]
#     vacancies = df_duration["Vacancies"]
#     return duration, vacancies

# def detailed_metric(current_df, detailed_sort):

#     df = current_df[current_df[detailed_sort] != 'ej angiven']
    
#     df = df.groupby(detailed_sort)["vacancies"].sum().sort_values(ascending=False).reset_index()
    
#     labels = df[detailed_sort]
#     cols = st.columns(len(df[detailed_sort]))
#     kpis = df["vacancies"]
#     return show_metric(labels, cols, kpis)
    
    
# def vacancies(df, input,field): 
#     return df[df["occupation_field"] == field].groupby(input)["vacancies"].sum().sort_values(ascending=False).reset_index()


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