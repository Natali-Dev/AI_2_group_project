# Jag vill arbeta i: välj stad
# Jag vill arbeta som: Välj occupation
# Jag vill arbeta hos: välj employer

# Skriv in en fråga, tex. Jag har många bollar i luften

import streamlit as st
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine
import numpy as np
from google import generativeai as oldGenai
from google.generativeai.types import GenerationConfig


def embedding_layout(current_df, field):
    st.markdown("## Hitta den bästa annonsen - med Gemini") 
    
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
    

    # st.write("Exempel på ord: Körkort, Högskoleexamen, Belastningsregister, Design, Lärling osv")
    user_question = st.text_input("Skriv in en fråga, eller ett ord: ")
    button = st.button("Starta gemini")
    if button: # and len(df_with_city_occupation) < 10: 
        st.write("Startar...", user_question)
        write_to_gemini(df_to_embedd, user_question)
        
        
def write_to_gemini(df, question):
    
    promt = f"""Du är en rekryterare inom Kropp och skönhetsvård.
    Svara på denna fråga och plocka ut den bästa annonsen: {question} 
    genom att läsa beskrivningarna i dessa jobbannonser: 
    {df[["headline", "description"]]}
    
    skriv även ut HELA beskrivningen för den annons du väljer, precis som den är. 
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
    
    
# EMBEDDING
# 1. Initiera embedding modell
# 2. Ha jobbanonnser redo
# 3. Embedda alla texter 
# 4. Ha en query 
# 5. Beräkna likheter med cosine
# 6. Skicka in till gemini

# def embedding_logic(df, query):
#     embedder = SentenceTransformer("intfloat/e5-small") #("intfloat/e5-base") # #Initiera modellen
    
#     query_embedding = embedder.encode("query: "+ query) #embedda queryn för snabbhet

#     value_list = []
#     for data in df["description"]:
#         doc_embedding = embedder.encode(data) #embedda varje description
#         similaritys = 1 - cosine(query_embedding, doc_embedding) # räkna ut likhetspoäng utifrån query
#         # if similaritys > 0.8:
#         value_list.append(similaritys) # Lägg in i lista
#         st.write(similaritys)
#     value_list
    
#     # Bästa indexet från listan
#     best_index = np.argmax(value_list)

#     if value_list[best_index] >= 0.8:
#         st.write(f"{best_index} - Hög likhet, här kommer annonsen som passar bäst")
#         best_text = df.iloc[best_index].reset_index(name="description")
#         st.write(best_text.iloc[4]["description"]) #DF har blivit omkastad 
#     else: 
#         st.write("Ingen annons matchade")