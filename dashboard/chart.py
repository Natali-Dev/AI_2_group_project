import plotly.express as px
import pandas as pd
import streamlit as st

# Creating a bar chart using Plotly Express
def bar_chart(df: pd.DataFrame, x: str, y: str, title: str):
    fig = px.bar(   
        df.sort_values(by=y, ascending=False), 
        x=x, 
        y=y, 
        #title=title,
        color=y,
        color_continuous_scale="Teal"               
    )
    fig.update_layout(xaxis_tickangle=-45)
    return fig


# Creating a pie chart using Plotly Express
def pie_chart(df: pd.DataFrame, names: str, values: str, title: str):
    fig = px.pie(df, names=names, values=values, hole=0.3) #title=title, )
    fig.update_traces(textposition="inside")
    return fig

# Show text in Streamlit
def display_text(text: str, title: str):
    st.subheader(title)
    st.write(text)

def display_data_table(df: pd.DataFrame, title: str):
    st.subheader(title)
    st.dataframe(df)

def load_city_coordinates(filepath: str) -> dict:
    city_coords = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            city, lat, lon = line.strip().split(",")
            city_coords[city] = (float(lat), float(lon))
    return city_coords

city_coordinates = load_city_coordinates("dashboard\swedish_cities.txt")


def add_coordinates(df):
    df["lat"] = df["workplace_city"].map(lambda city: city_coordinates.get(city, (None, None))[0])
    df["lon"] = df["workplace_city"].map(lambda city: city_coordinates.get(city, (None, None))[1])
    return df.dropna(subset=["lat", "lon"])

def map_chart(df: pd.DataFrame, title: str = "Antal lediga jobb per stad"):
    df = df.copy()
    df["Antal jobb"] = 1
    df = add_coordinates(df)

    city_vacancies = df.groupby(["workplace_city", "lat", "lon"])["Antal jobb"].sum().reset_index()
    city_vacancies = city_vacancies.rename(columns={"workplace_city": "Stad"})

    fig = px.scatter_mapbox(
        city_vacancies,
        lat="lat",
        lon="lon",
        size="Antal jobb",
        color="Antal jobb",
        hover_name="Stad",
        size_max=30,
        zoom=4.5,
        mapbox_style="carto-positron",
        title=title,
        color_continuous_scale="Viridis"
    )

    fig.update_layout(
        mapbox_center={"lat": 62.0, "lon": 16.0},  
        mapbox_zoom=4.5, 
        margin={"r":0,"t":50,"l":0,"b":0}
    )

    return fig


# Detailed_overview: Metod för att få ut barplot, används i kolumn 1, workplace city, employer name, occupation
def chart_top_occupations(current_df, sort_on, field):

    df = current_df.groupby(sort_on)["vacancies"].sum().sort_values(ascending=False).reset_index()
    bar = st.slider("Antal staplar att visa", min_value=10, max_value=20, step=1)

    fig = px.bar(df.head(bar), x=sort_on, y="vacancies", color="vacancies",color_continuous_scale="Teal", labels={"workplace_city": "Arbetsort", "employer_name": "Arbetsgivare", "occupation": "Yrke", "vacancies": "Antal"})
    # fig.update_layout(title_text=f"Topp {bar} {sort_on}s with most vacancies in field: {field}")
    return fig, df

#Detaied_overview: Metod för att få ut pie-chart, används i kolumn 2, languages, duration, working hours type
def general_pie_chart(current_df, sort_on,get_unique, detailed_sort):

    df = current_df[current_df[detailed_sort] != 'ej angiven']
    df = df[df[sort_on] == get_unique]
    fig =  px.pie(df.groupby(detailed_sort)["vacancies"].sum().reset_index(), names=detailed_sort, values="vacancies", hole=0.2)
    length = df["vacancies"].sum()
    return fig, length





