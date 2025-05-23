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


# Detailed_overview: Metod för att få ut barplot, används i kolumn 1, workplace city, employer name, occupation
def chart_top_occupations(current_df, sort_on, field):

    df = current_df.groupby(sort_on)["vacancies"].sum().sort_values(ascending=False).reset_index()
    bar = st.slider("Antal staplar att visa", min_value=10, max_value=20, step=1)

    fig = px.bar(df.head(bar), x=sort_on, y="vacancies", color="vacancies",color_continuous_scale="Teal" )
    # fig.update_layout(title_text=f"Topp {bar} {sort_on}s with most vacancies in field: {field}")
    return fig, df

#Detaied_overview: Metod för att få ut pie-chart, används i kolumn 2, languages, duration, working hours type
def general_pie_chart(current_df, sort_on,get_unique, detailed_sort):

    df = current_df[current_df[detailed_sort] != 'ej angiven']
    df = df[df[sort_on] == get_unique]
    fig =  px.pie(df.groupby(detailed_sort)["vacancies"].sum().reset_index(), names=detailed_sort, values="vacancies", hole=0.2)
    length = df["vacancies"].sum()
    return fig, length





