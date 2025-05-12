import plotly.express as px
import pandas as pd
import streamlit as st

# Creating a bar chart using Plotly Express
def bar_chart(df: pd.DataFrame, x: str, y: str, title: str):
    fig = px.bar(df, x=x, y=y, title=title)
    return fig


# Creating a pie chart using Plotly Express
def pie_chart(df: pd.DataFrame, names: str, values: str, title: str):
    fig = px.pie(df, names=names, values=values, title=title, holes=0.3)
    return fig

# Show text in Streamlit
def display_text(text: str, title: str):
    st.subheader(title)
    st.write(text)




#show map with plotly express
def map_chart(df: pd.DataFrame, loc:str = "Stad", color:str = "Antal jobb", title:str="Antal lediga jobb per stad"):
    # Create a DataFrame with the sum of 'vacancies' for each city
    city_vacancies = df.groupby(loc)[color].sum().reset_index()

    fig = px.choropleth(city_vacancies,
                        location=loc,
                        locationmode="Städer namn",)



