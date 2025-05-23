
from google import genai
import os
from dotenv import load_dotenv
import duckdb
import json
load_dotenv()
from google import generativeai as oldGenai
from google.generativeai.types import GenerationConfig
import plotly.express as px
import streamlit as st
import pandas as pd
# from gemini import gemini_layout

def gemini_chunks_layout(current_df, field): 
    
    # current_df = current_df.sort_values(by="vacancies", ascending=False)
    st.markdown("## Ställ en fråga till Gemini") 
    category = st.selectbox(
        "Välj en kategori:", "occupation" #["workplace_city", "employer_name", "occupation"]
    )
    choice_unique = st.selectbox(
        "välj en stad/arbetsgivare/yrke", "Journalist/Reporter"#current_df[category].unique()
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
    # st.write(current_df.groupby("occupation")["vacancies"].sum().sort_values(ascending=False).reset_index().head(15))


    if choice_question != "Select...": #För att den inte ska köra innan man faktiskt klickat på en fråga
        # Skriver ut DF så man kan se vacancies
        top_employer = current_df.groupby(category)[["vacancies", "description"]].sum().sort_values(by="vacancies", ascending=False).reset_index()
        #Skriver ut DF som är det du valt
        user_choice = top_employer[top_employer[category] == choice_unique]
        #Spara till textfil
        user_choice.to_csv("for_gemini_chunks.txt")
        
        #Skriv ut den annons som 
        st.write(user_choice)
        gemini_chunks_logic(field)
    
    
    
def gemini_chunks_logic(field):
    
    model, response_list = gemini_first_promt(field)
    response_sum = gemini_second_promt(model, response_list)
    df_krav, df_merit, df_sammanfattning = convert_second_promt_to_df(response_sum)
    st.write(df_sammanfattning["sammanfattning"])
    
    fig_krav, fig_merit = plot_gemini(df_krav, df_merit)
    st.plotly_chart(fig_krav)
    st.plotly_chart(fig_merit)



def gemini_first_promt(field):
    with open("for_gemini_chunks.txt", "r", encoding='utf-8') as file: 
        ad_text = file.read() 

    max_rows = 100
    ad_text_splitted = ad_text.split("\n") #tagit bort alla mellanslag
    chunks = [] # lista för textbitar

    for i in range(0, len(ad_text_splitted), max_rows): 
        chunk = "\n".join(ad_text_splitted[i:i+max_rows])
        chunks.append(chunk)

    response_list = []
    for chunk in chunks:
        promt = f"""Du är en rekryterare inom {field}.
        Plocka ut max 3 av vanligaste kraven och max av 3 vanligaste meriterade och antal av dessa som efterfrågas i dessa jobbannonser, samt en sammanfattning av krav och meriter som du skriver ut (om det finns):
        {chunk}

        Output ska vara i detta formatet enbart: 

        {{
            "sammanfattning": ["sammanfattning"]
            "krav": [erfarenhet1, erfarenhet2, ...]
            "antal krav": [summa erfarenhet1..]
            "meriterande": [meriterande1,meriterande2, ... ]
            "antal meriterande": [summa meriterande1..]
            
        }}
        """
        model = oldGenai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=GenerationConfig(
                temperature=0.0,         
                top_p=1.0,  # Säkerställer att sampling inte påverkas   #verkar inte göra skillnad
                top_k=1     # Tar bort variation)                       #verkar inte göra skillnad    
            )
        )
        response = model.generate_content(promt)
        st.write(response.text) # Skriver ut varje promt
        response_list.append(response.text)
                    # with open("response_list.txt", "w") as text_file: 
                    #     text_file.write(response_list.text)
    return model, response_list
    

def gemini_second_promt(model, response_list):
    second_promt = f"""Kan du summera dessa dictionarys till en enda dictionary? Sammanfattningen ska vara enbart en summering av alla dem: 
    {response_list}

    Output ska vara i detta formatet enbart: 

        {{
            "sammanfattning": ["sammanfattning"]
            "krav": [erfarenhet1, erfarenhet2, ...]
            "antal krav": [summa erfarenhet1..]
            "meriterande": [meriterande1,meriterande2, ... ]
            "antal meriterande": [summa meriterande1..]
            
        }}
        """
    response_sum = model.generate_content(second_promt)
    print(response_sum.text)
    return response_sum


def convert_second_promt_to_df(response_sum):
    data = response_sum.text
    cleaned = data.strip("```json") #.replace("\n", "").strip().replace("  ", "")
    data = json.loads(cleaned)

    df_krav = pd.DataFrame({
    "krav": data["krav"], 
    "antal krav": data["antal krav"]
    })
    
    df_merit = pd.DataFrame({
    "meriterande": data["meriterande"],
    "antal meriterande": data["antal meriterande"]
    })
    
    df_sammanfattning = pd.DataFrame({
    "sammanfattning": data["sammanfattning"]
    })
    
    st.write(df_krav)
    st.write(df_merit)
    st.write(df_sammanfattning)
    
    return df_krav, df_merit, df_sammanfattning

def plot_gemini(df_krav, df_merit):
    fig_krav = px.bar(df_krav, y="antal krav", x="krav")
    fig_meriterande = px.bar(df_merit, y="antal meriterande", x="meriterande")
    return fig_krav, fig_meriterande
