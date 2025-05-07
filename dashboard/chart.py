from kpi import df_mart
import plotly.express as px
import streamlit as st
# i df:arna, vilket occupation har högst andel lediga tjänster

def vacancies(df, input,field): 
    return df[df["occupation_field"] == field].groupby(input)["vacancies"].sum().sort_values(ascending=False).reset_index()

def chart_top_occupations(field, sort_on):

    df = vacancies(df_mart, sort_on, field)
    if field == "Alla": 
        df = df_mart.groupby(sort_on)["vacancies"].sum().sort_values(ascending=False).reset_index().head(10)
        
    fig = px.bar(df.head(10), x=sort_on, y="vacancies")
    fig.update_layout(title_text=f"Top 10 {sort_on}s with most vacancies in field: {field}")
    return fig

def field_pie_chart():
    mart_full_time = df_mart.groupby("occupation_field")["vacancies"].sum().sort_values(ascending=False).reset_index(name="total vacancies")
    pie_fig = px.pie(mart_full_time,values="total vacancies",names="occupation_field",width=350, height=350)
    return pie_fig
