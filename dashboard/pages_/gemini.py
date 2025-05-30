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

def gemini_layout(current_df, field):

    current_df.sort_values(by="vacancies")
    st.markdown(f"## Ställ en fråga till Gemini - {field}") 
    # category = st.selectbox(
    #     "Välj en kategori:", ["workplace_city", "employer_name", "occupation"]
    # )
    # choice_unique = st.selectbox(
    #     "välj en stad/arbetsgivare/yrke", current_df[category].unique()
    # )
    df = current_df.groupby("workplace_city")["vacancies"].sum().sort_values(ascending=False).reset_index() #Sortera df på mest lediga jobb per stad
    city = st.selectbox("Jag vill arbeta i", df["workplace_city"]) # Välj en stad
    
    df_with_city = current_df[current_df["workplace_city"] == city] #Hämta ut df där stad är = city från selectbox
    df = df_with_city.groupby("occupation")["vacancies"].sum().sort_values(ascending=False).reset_index() #sortera df på mest lediga jobb per yrke
    # st.write(df_with_city)
    
    
    occupation = st.selectbox("Jag vill arbeta som", df["occupation"]) # Välj ett yrke
    df_with_city_occupation = df_with_city[df_with_city["occupation"] == occupation] # hämta ut df sorterad på stad och yrke valda i selectbox
    df = df_with_city_occupation.groupby("employer_name")["vacancies"].sum().sort_values(ascending=False).reset_index() #Sortera df på mest lediga jobb per arbetsgivare
    
    if len(df_with_city_occupation) >= 20: # Om det är för många annonser
        employer = st.selectbox("Jag vill arbeta hos (valfritt?)", df["employer_name"]) #Välj employer_name 
        df_with_city_employer_occupation = df_with_city_occupation[df_with_city_occupation["employer_name"] == employer] # hämta ut df sorterad på stad, yrke och occupation vald i selectbox
        
        df_to_embedd = df_with_city_employer_occupation.reset_index()
        st.write(df_to_embedd[["headline", "occupation", "occupation_field", "vacancies", "description"]]) #Skriv ut annonser
        
    elif len(df_with_city_occupation) <= 19: 
        df_to_embedd = df_with_city_occupation.reset_index()
        st.write(df_to_embedd[["headline", "occupation", "occupation_field", "vacancies", "description"]]) #Skriv ut annonser
        question_1 = "Vad är de vanligaste kraven och meriterna?"
        question_2 = "Vad är de vanligaste arbetsuppgifterna?"
        question_3 = "Vilka personliga egenskaper krävs?"
        question_4 = ""
    choice_question = st.selectbox(
        "Välj en fråga",
        [
            "Select...",
            question_1,# inom {choice_unique}?",
            question_2,# inom {choice_unique}?",
            question_3,
        ],
    )

    if choice_question != "Select...": #För att den inte ska köra innan man faktiskt klickat på en fråga
        button = st.button("Starta Gemini")
        if button:
            text = gemini_logic(current_df,df_to_embedd, choice_question, field) 
            # st.write(text.text)
            df_krav, df_merit, df_sammanfattning = convert_prompt_to_df(text)
            fig_krav, fig_merit = plot_gemini(df_krav, df_merit)
            st.write(df_sammanfattning["sammanfattning"][0])
            st.plotly_chart(fig_krav)
            st.plotly_chart(fig_merit)
            
def get_right_promt(question):
    question_1 = "Vad är de vanligaste kraven och meriterna?"
    question_2 = "Vad är de vanligaste arbetsuppgifterna?"
    question_3 = "Vilka personliga egenskaper krävs?"
    if question == question_1: 
        prompt = ""
    elif question == question_2:
        prompt = ""
    elif question == question_3: 
        prompt = ""
        
    return prompt
    

def gemini_logic(current_df,df_to_embedd, choice_question, field):
    # top_employer = (current_df.groupby(category)[["vacancies", "description"]].sum().sort_values(by="vacancies", ascending=False).reset_index())
    # user_choice = top_employer[top_employer[category] == choice_sort]
    user_choice = df_to_embedd
    # st.write(user_choice)

    # user_choice.to_csv("for_gemini.txt")


    # with open("for_gemini.txt", "r", encoding="utf-8") as file:
    #     ad_text = file.read()

    # Svara på denna fråga: {choice_question} Genom att läsa dessa annonser.
    prompt = f"""Du är en rekryterare inom {field}.
    Läs dessa jobbannonser:
    {user_choice["description"]}
    -----SLUT PÅ ANNONSER-------
    Plocka ut 1-5 av de vanligaste kraven/kvalifikationer och antal av dessa.
    Plocka ut 1-5 av de vanligaste meriterade/bonus och antal av dessa.  
    Skriv en sammanfattning av det som du summerat.

    Returnera ingenting annat än resultatet strikt i följande JSON-format: 

        {{
            "krav": [erfarenhet1, erfarenhet2, ...],
            "antal krav": [summa erfarenhet1, summa erfarenhet2, ...],
            "meriterande": [meriterande1,meriterande2, ... ],
            "antal meriterande": [summa meriterande1, summa meriterande2, ...],
            "sammanfattning": ["sammanfattning"]
            
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
    # response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    response = model.generate_content(prompt)


    return response



def convert_prompt_to_df(response):
    data = response.text
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
    
    # st.write(df_krav)
    # st.write(df_merit)
    # st.write(df_sammanfattning)
    
    return df_krav, df_merit, df_sammanfattning

def plot_gemini(df_krav, df_merit):
    fig_krav = px.bar(df_krav, y="antal krav", x="krav")
    fig_meriterande = px.bar(df_merit, y="antal meriterande", x="meriterande")
    return fig_krav, fig_meriterande

