import streamlit as st
import plotly.express as px
import os
from google import genai
import os
import pandas as pd
import json
from dotenv import load_dotenv
from google import generativeai as oldGenai
from google.generativeai.types import GenerationConfig
import duckdb

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

question_1 = "Vad är de vanligaste kraven?"
question_2 = "Vad är de vanligaste meriterande kunskaperna?"
question_3 = "Vad är de vanligaste arbetsuppgifterna?"
question_4 = "Vilka personliga egenskaper krävs?"

def gemini_layout(current_df, field):

    st.markdown(f"## Ställ en fråga till Gemini - {field}") 

    df = current_df.groupby("workplace_city")["vacancies"].sum().sort_values(ascending=False).reset_index() #Sortera df på mest lediga jobb per stad
    city = st.selectbox("Jag vill arbeta i", df["workplace_city"]) # Välj en stad
    
    df_with_city = current_df[current_df["workplace_city"] == city] #Hämta ut df där stad är = city från selectbox
    df = df_with_city.groupby("occupation")["vacancies"].sum().sort_values(ascending=False).reset_index() #sortera df på mest lediga jobb per yrke

    occupation = st.selectbox("Jag vill arbeta som", df["occupation"]) # Välj ett yrke
    df_with_city_occupation = df_with_city[df_with_city["occupation"] == occupation] # hämta ut df sorterad på stad och yrke valda i selectbox
    df = df_with_city_occupation.groupby("employer_name")["vacancies"].sum().sort_values(ascending=False).reset_index() #Sortera df på mest lediga jobb per arbetsgivare
    
    if len(df_with_city_occupation) >= 20: # Om det är för många annonser
        employer = st.selectbox("Jag vill arbeta hos", df["employer_name"]) #Välj employer_name 
        df_with_city_employer_occupation = df_with_city_occupation[df_with_city_occupation["employer_name"] == employer] # hämta ut df sorterad på stad, yrke och occupation vald i selectbox
        
        df_to_use = df_with_city_employer_occupation.reset_index()
        st.write(df_to_use[["headline", "occupation", "occupation_field", "vacancies", "description"]]) #Skriv ut annonser
        
    elif len(df_with_city_occupation) <= 19: 
        df_to_use = df_with_city_occupation.reset_index()
        st.write(df_to_use[["headline", "occupation", "occupation_field", "vacancies", "description"]]) #Skriv ut annonser
    
    choice_question = st.selectbox(
        "Välj en fråga",
        [
            "Select...",
            question_1,# inom {choice_unique}?",
            question_2,# inom {choice_unique}?",
            question_3,
            question_4
        ],
    )


    button = st.button("Starta Gemini") #För att den inte ska köra direkt
    if button:
        response = gemini_logic(df_to_use, choice_question, field) 
        
        df_krav, df_sammanfattning = convert_prompt_to_df(response, choice_question)
        
        fig_krav= plot_gemini(df_krav)
        
        st.write(df_sammanfattning["sammanfattning"][0])
        st.plotly_chart(fig_krav)
            

def gemini_logic(df_to_use, choice_question, field):


    prompt = get_right_promt(choice_question)

    text_list = df_to_use["description"].tolist()

    prompt = f"""Du är en rekryterare inom {field}.
    Läs denna lista med 7 olika jobbannonser:
    {text_list}
    
    -----SLUT PÅ ANNONSER-------
    
    {prompt}
    
    """

    model = oldGenai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=GenerationConfig(
        temperature=0.0,         
        top_p=1.0,  # Säkerställer att sampling inte påverkas   
        top_k=1     # Tar bort variation)                          
    )
)
    response = model.generate_content(prompt)


    return response

def get_right_promt(question):

    if question == question_1: 
        prompt = f"""    
    Plocka ut 1-5 av de vanligaste kraven/kvalifikationer och antal av dessa.
    Skriv en sammanfattning av det som du summerat.

    Returnera ingenting annat än resultatet strikt i följande JSON-format: 

        {{
            "krav": [erfarenhet1, erfarenhet2, ...],
            "antal krav": [summa erfarenhet1, summa erfarenhet2, ...],
            "sammanfattning": ["sammanfattning"]
            
        }}"""
    elif question == question_2: 
                prompt = f"""    
    Plocka ut 1-5 av de vanligaste meriterade/önskvärda kunskaperna och antal av dessa.  
    Skriv en sammanfattning av det som du summerat.

    Returnera ingenting annat än resultatet strikt i följande JSON-format: 

        {{
            "meriterande": [meriterande1,meriterande2, ... ],
            "antal meriterande": [summa meriterande1, summa meriterande2, ...],
            "sammanfattning": ["sammanfattning"]
            
        }}"""
    elif question == question_3:
        prompt =  f"""   
    Plocka ut 1-5 av de vanligaste arbetsuppgifterna och antal av dessa.
    Skriv en sammanfattning av det som du summerat.

    Returnera ingenting annat än resultatet strikt i följande JSON-format: 

        {{
            "arbetsuppgift": [arbetsuppgift1, arbetsuppgift2, ...],
            "antal arbetsuppgift": [summa arbetsuppgift1, summa arbetsuppgift2, ...],
            "sammanfattning": ["sammanfattning"]
            
        }}
        """
    elif question == question_4: 
        prompt =  f"""   Plocka ut 1-5 av de vanligaste personliga egenskaper som krävs och antal av dessa.
    Plocka ut 1-5 av de vanligaste meriterade/bonus och antal av dessa.  
    Skriv en sammanfattning av det som du summerat.

    Returnera ingenting annat än resultatet strikt i följande JSON-format: 

        {{
            "personlig": [personlig1, personlig2, ...],
            "antal personlig": [summa personlig1, summa personlig2, ...],
            "sammanfattning": ["sammanfattning"]
            
        }}
        """
        
    return prompt
    


def convert_prompt_to_df(response, question):
    data = response.text
    cleaned = data.strip("```json")
    data = json.loads(cleaned)

    # keylist = []
    # valuelist = []
    
    if question == question_1:
        df_krav = pd.DataFrame({
        "krav": data["krav"], 
        "antal krav": data["antal krav"]
        })
        
    elif question == question_2: 
        df_krav = pd.DataFrame({
        "meriterande": data["meriterande"],
        "antal meriterande": data["antal meriterande"]
        })
        
    elif question == question_3: 
        df_krav = pd.DataFrame({
            "arbetsuppgift": data["arbetsuppgift"],
            "antal arbetsuppgift": data["antal arbetsuppgift"]
        })
        
    elif question == question_4: 
        df_krav = pd.DataFrame({
            "personlig": data["personlig"],
            "antal personlig": data["antal personlig"]
        })
        
        
    df_sammanfattning = pd.DataFrame({
    "sammanfattning": data["sammanfattning"]
    })

    return df_krav, df_sammanfattning

def plot_gemini(df_krav):
    st.write(df_krav)

    column_names = df_krav.columns
    fig_krav = px.bar(df_krav, y=column_names[1], x=column_names[0])
    return fig_krav