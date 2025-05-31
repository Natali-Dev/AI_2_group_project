import streamlit as st
import plotly.express as px
import os
from google import genai
import os
import pandas as pd
import json
from dotenv import load_dotenv
import duckdb

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def gemini_layout(current_df, field):

    # sort_on = st.selectbox("Sortera på", ["Workplace City", "employer_name", "occupation"])
    # fig = chart_top_occupations(field, sort_on)
    # st.plotly_chart(fig)
    # vilken utbildning krävs? #belasningsregister #i vilken stad finns minst krav och vilka är dessa #vilken stad har mest krav
    # Matcha person med jobb, skriva in nyckelord och sök efter matchande annonser i städer/ hos arbetsgivare / på yrken
    
    st.markdown("## Ställ en fråga till Gemini") 
    category = st.markdown("## Ställ en fråga till Gemini"); category = {"Arbetsort": "workplace_city", "Arbetsgivare": "employer_name", "Yrke": "occupation"}[st.selectbox("Välj en kategori:", ["Arbetsort", "Arbetsgivare", "Yrke"])]

    choice_unique = st.selectbox(
        "välj en stad/arbetsgivare/yrke", current_df[category].sort_values().unique()
    )
    choice_question = st.selectbox(
        "Välj en fråga",
        [
            "Select...",
            f"Vad är de vanligaste kraven och meriterna inom {choice_unique}?",
            f"Vad är de vanligaste arbetsuppgifterna inom {choice_unique}?",
            f"",
        ],
    )

    if choice_question != "Select...": #För att den inte ska köra innan man faktiskt klickat på en fråga
        text = gemini_logic(current_df,category, choice_unique, choice_question) 
        st.write(text)
        
    # choice_input = st.text_input(f"Ställ en egen fråga", {choice_sort})
    # st.write(text)
    # st.write() #sammanfattning av datan
        
    # fig_krav, fig_meriterande = plot_gemini(text)
    # st.plotly_chart(fig_krav)
    # st.plotly_chart(fig_meriterande)
    # utgå ifrån vilken field som är vald


def gemini_logic(current_df,category, choice_sort, choice_question):
    top_employer = (
        current_df.groupby(category)[["vacancies", "description"]]
        .sum()
        .sort_values(by="vacancies", ascending=False)
        .reset_index()
    )
    user_choice = top_employer[top_employer[category] == choice_sort]
    st.write(user_choice)

    user_choice.to_csv("for_gemini.txt")


    with open("for_gemini.txt", "r", encoding="utf-8") as file:
        ad_text = file.read()

    promt = f"""Du är en rekryterare inom Media, Kultur, Design.
    Svara på denna fråga: {choice_question} Genom att läsa dessa annonser, sammanfattat: 
    {ad_text}

    """

    response = client.models.generate_content(model="gemini-2.0-flash", contents=promt)
    print(response.text)
    text = response.text


    return text



