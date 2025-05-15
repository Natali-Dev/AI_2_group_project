import plotly.express as px
import pandas as pd
import streamlit as st

# Creating a bar chart using Plotly Express
def bar_chart(df: pd.DataFrame, x: str, y: str, title: str):
    fig = px.bar(df, x=x, y=y, title=title)
    return fig


# Creating a pie chart using Plotly Express
def pie_chart(df: pd.DataFrame, names: str, values: str, title: str):
    fig = px.pie(df, names=names, values=values, title=title, hole=0.3)
    return fig

# Show text in Streamlit
def display_text(text: str, title: str):
    st.subheader(title)
    st.write(text)

def display_data_table(df: pd.DataFrame, title: str):
    st.subheader(title)
    st.dataframe(df)



#show map with plotly express
def map_chart(df: pd.DataFrame, title: str = "Antal lediga jobb per stad"):
    # Kopiera df så du inte modifierar originalet
    df = df.copy()

    
    df["Antal jobb"] = 1

    
    city_vacancies = df.groupby("workplace_city")["Antal jobb"].sum().reset_index()
    city_vacancies = city_vacancies.rename(columns={"workplace_city": "Stad"})

    fig = px.choropleth(
        city_vacancies,
        locations="Stad",
        locationmode="country names", 
        color="Antal jobb",
        hover_name="Stad",
        color_continuous_scale="Viridis",
        title=title
    )

    fig.update_geos(fitbounds="locations", visible=True)
    return fig





