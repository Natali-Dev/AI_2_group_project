import sys
import os
import streamlit as st
import pandas as pd
import time
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

#Lägg in funktioner från llm_core 
# Exempel:

try:
    from llm_core.interaction import query_text_to_sql, query_rag_model
    # from llm_core.utility import get_db_connection # Om vi behöver ansluta till DB här
    LLM_FUNCTIONS_IMPORTED = True
except ImportError as e:
    st.error(f"Kunde inte importera LLM-funktioner: {e}. Vissa delar kommer använda dummy-data.")
    LLM_FUNCTIONS_IMPORTED = False
    # Dummy-funktioner så sidan kan ritas upp.
    def query_text_to_sql(user_query_string, db_path, llm_api_key):
        time.sleep(1)
        return f"SELECT '{user_query_string}' AS SimulatedSQL;", pd.DataFrame({'Resultat': ['Ingen riktig data']})
    def query_rag_model(query_text, db_path, llm_api_key):
        time.sleep(1)
        return f"Simulerat RAG-svar för: '{query_text}'", ["Simulerad kontext 1", "Simulerad kontext 2"]
    

# --- API-nyckel och Databassökväg ---

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("VARNING: GEMINI_API_KEY saknas i .streamlit/secret.toml.")
    GEMINI_API_KEY = None

DB_PATH = os.path.join(project_root, "ads_data.duckdb")
if not os.path.exists(DB_PATH) and LLM_FUNCTIONS_IMPORTED: # Varna bara om vi försöker använda riktiga funktioner
    st.error(f"Databasfilen ads_data.duckdb hittades inte på förväntad plats: {DB_PATH}.")


def build_llm_introduction_and_tools():
    st.set_page_config(page_title="LLM Dashboard", page_icon="🤖", layout="wide")
    st.title("Välkommen till LLM Dashboarden")
    st.markdown("""
    Här kan du interagera med våra avancerade språkmodeller(LLM) för att få insikter från jobbannonsdata
    på nya och spännande sätt! Nedan hittar du en kort förklaring av de verktyg som finns tillgängliga
    och sedan kan du välja ett verktyg via flikarna.
    """)
    st.divider()
    col1,col2 = st.columns(2)
    with col1:
        st.subheader("Text-to-SQL: Fråga Databasen med Vanligt Språk")
        st.markdown("""
        Har du en fråga som du tror datan i vår strukturerade databas kan svara på?
        Skriv din fråga på svenska, så kommer vår LLM att försöka översätta den till en SQL-kod.
        SQL-koden körs sedan mot databasen ('ads_data.duckdb', 'refined'-schemat) och du får tillbaka resultatet!
                    
        **Exempel på frågor:**
        * "Vilka Data/IT-jobb finns i göteborg?"
        * "Hur många jobb kräver B-körkort?"
        * "Visa de 5 vanligaste yrkestitlarna."
        """)
    with col2:
        st.subheader(" RAG (Retrieval-Augmented Generation): Fråga Annonsinnehåll")
        st.markdown("""
        Vill du veta mer om vad som faktiskt står i textbeskrivningarna i jobbannonserna?
        Med RAG-verktyget kan du ställa frågor om detta. Modellen letar först upp relevanta textavsnitt
        från annonserna och använder sedan dessa som underlag för att formulera ett svar.
        
        **Exempel på frågor:**
        * "Vilka kompetenser efterfrågas ofta för projektledare?"
        * "Nämns det något om möjligheter till distansarbete?
        * "Vilka tekniska färdigheter är vanliga för systemutvecklare?
        """)
    st.divider()


    # --- Flikar för det faktiska verktygen ---
    tab_text_to_sql, tab_rag = st.tabs(["Prova Text-to-SQL", "Prova RAG"])

    with tab_text_to_sql:
        st.header("Verktyg: Text-to-SQL")
        with st.form("text_to_sql_form"):
            sql_query_text = st.text_area("Ställ din fråga till databasen:", height=100, placeholder="Exempel: Vilka jobb finns i Göteborg inom IT?")
            sql_submit_button = st.form_submit_button("Kör SQL-fråga")

            if sql_submit_button and sql_query_text:
                if not GEMINI_API_KEY and LLM_FUNCTIONS_IMPORTED:
                    st.error("GEMINI_API_KEY saknas i .streamlit/secrets.toml. Kan inte köra den riktiga modellen.")
                else:
                    with st.spinner("Bearbetar din SQL-fråga..."):
                        # Anropa din riktiga funktion eller dummy-funktionen
                        genreated_sql, result_df = query_text_to_sql(sql_query_text, DB_PATH, GEMINI_API_KEY)

                        st.subheader("Genererad SQL-fråga:")
                        st.code(genreated_sql, language="sql")
                        
                        st.subheader("Resultat:")
                        if result_df is not None and not result_df.empty:
                            st.dataframe(result_df, use_container_width=True)
                        elif result_df is not None:
                            st.info("Inga resultat hittades för din fråga.")
                        else:
                            st.warning("Kunde inte hämta några resultat. Något som inte är klart.")
    
    with tab_rag:
        st.header("Verktyg: RAG - Fråga Annonsinnehåll")
        with st.form("rag_form"):
            rag_query_text = st.text_area ("Ställ din fråga om innehållet i jobbannonserna: ", height=100, placeholder= "Exempel: Vilka kompetenser efterfrågas ofta för projektledare?")
            rag_submit_button = st.form_submit_button("Ställ RAG-fråga")

            if rag_submit_button and rag_query_text:
                if not GEMINI_API_KEY and LLM_FUNCTIONS_IMPORTED:
                    st.error("API-nyckel för Gemini saknas. Kan inte köra den riktiga modellen.")
                else:
                    with st.spinner("Bearbetar din RAG-fråga..."):
                        # Anropa din riktiga funktion eller dummy-funktionen
                        answer, context_chunks = query_rag_model(rag_query_text, DB_PATH, GEMINI_API_KEY)

                        st.subheader("Svar från RAG-modellen:")
                        st.markdown(f"> {answer}") # Använd blockquote för tydlighet

                        if context_chunks:
                            with st.expander("Visa använd kontext (hämtade täxtavsnitt)", expanded= False):
                                for i, chunk in enumerate(context_chunks):
                                    st.text_area(f"Avsnitt {i+1}", chunk, height= 100, disabled=True, key = f"rag_chunk_{i}")
                        else:
                            st.info("Ingen specifik kontext hittades för din fråga.")
    st.divider()
    st.info("""
    **Observera:** Om LLM-funktionerna intek unde importeras korrekt eller om API-nyckeln saknas,
    används exempeldata/simulerade svar. För full funktionalitet, se till att 'llm_core.interaction.py'
    är korrekt konfiguerad med dina funktioner och att 'GEMINI_API_KEY' finns i 'secrets.toml'.
    """)

# --- Kör huvudfunktionen för att bygga sidan ---
build_llm_introduction_and_tools()
