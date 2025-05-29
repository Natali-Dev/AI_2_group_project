import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Importera dina egna moduler (justera sökvägar vid behov)
from llm_core.interaction import (
    get_gemini_model,
    determine_intention, # Antag att denna funktion finns och är redo
    get_llm_response_to_query_with_rag_WITHOUT_db,
    get_llm_response_to_query_without_rag_or_db,
    get_sql_from_llm,
    # Överväg en funktion för att summera DataFrame med LLM
    # def summarize_dataframe_with_llm(model, dataframe, query): ...
)
from llm_core.db_executor import (
    get_db_connection, # Ska returnera en DuckDB-anslutning
    get_schema,
    execute_sql_query
)
from rag_pipeline.setup_embedding_db import (
    load_vector_store, # Laddar FAISS-index
    get_similar_docs
)

# För moderna UI-komponenter (om du vill använda dem mer)
try:
    from streamlit_shadcn_ui import slider, input, textarea, button, switch, alert, card, tabs # Exempel
    import streamlit_shadcn_ui as sui # För att kalla funktioner som sui.button etc.
    shadcn_available = True
except ImportError:
    shadcn_available = False
    st.warning("streamlit-shadcn-ui är inte installerad. Vissa UI-element kan se annorlunda ut.")

# Ladda miljövariabler (t.ex. GEMINI_API_KEY)
load_dotenv()

# --- Konfiguration och Initialisering (cachas) ---
@st.cache_resource # Viktigt för prestanda
def initialize_agent_components():
    """
    Initialiserar och returnerar de nödvändiga komponenterna för agenten.
    """
    try:
        model = get_gemini_model() # Din funktion för att hämta Gemini-modellen
    except Exception as e:
        st.error(f"Kunde inte ladda Gemini-modellen: {e}")
        st.stop()
        return None, None, None

    try:
        vector_store = load_vector_store() # Din funktion för att ladda FAISS-index
        if vector_store is None:
            st.warning("Kunde inte ladda FAISS vector store. RAG-funktionalitet kommer att vara begränsad.")
    except Exception as e:
        st.error(f"Fel vid laddning av FAISS vector store: {e}")
        vector_store = None


    db_schema_info = None
    try:
        # Hämta databasschema för text-to-SQL
        # Du kan behöva anpassa detta för att få ett koncis och användbart schema för LLM:en
        conn = get_db_connection()
        if conn:
            db_schema_info = get_schema(conn, format_for_llm=True) # Antag att get_schema kan formatera för LLM
            conn.close()
        else:
            st.warning("Kunde inte ansluta till databasen. SQL-funktionalitet kommer att vara begränsad.")
    except Exception as e:
        st.error(f"Fel vid hämtning av databasschema: {e}")
        db_schema_info = None # Säkerställ att den är None om fel uppstår

    return model, vector_store, db_schema_info

# Ladda komponenter
llm_model, faiss_vector_store, db_schema = initialize_agent_components()

# --- Huvudfunktion för JobbAgenten Dashboard ---
def job_agent_dashboard():
    """
    Huvudfunktionen som renderar JobbAgentens dashboard och hanterar interaktioner.
    """
    st.set_page_config(layout="wide", page_title="🤖 JobbAgenten Deluxe", page_icon="🤖")

    # Anpassad CSS (om du har en style.css och vill använda den)
    # try:
    #     with open("style.css") as f:
    #         st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    # except FileNotFoundError:
    #     pass # Ingen fara om filen inte finns

    if shadcn_available:
        cols = st.columns([0.8, 0.2])
        with cols[0]:
            st.title("🤖 JobbAgenten Deluxe")
            st.caption("Din intelligenta assistent för att utforska jobbannonser och datainsikter.")
        with cols[1]:
            if st.button("Rensa chatt", type="secondary", key="clear_chat_btn_main"):
                 st.session_state.messages = []
                 st.rerun()

    else:
        st.title("🤖 JobbAgenten Deluxe")
        st.caption("Din intelligenta assistent för att utforska jobbannonser och datainsikter.")
        if st.button("Rensa chatt"):
            st.session_state.messages = []
            st.rerun()


    # --- Initiera chatt-historik ---
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hej! Hur kan jag hjälpa dig att utforska jobbannonser idag?"}
        ]

    # --- Visa chattmeddelanden ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Visa källor om de finns
            if "sources" in message and message["sources"]:
                with st.expander("Visade källor (RAG)", expanded=False):
                    for i, source_doc in enumerate(message["sources"]):
                        source_name = source_doc.metadata.get("source", f"Källa {i+1}")
                        if shadcn_available:
                            with card(key=f"source_card_{message['role']}_{i}"): # Unikt nyckel för varje kort
                                st.subheader(f"📄 {source_name}")
                                st.caption(f"Relevans: {source_doc.metadata.get('score', 'N/A'):.2f}" if isinstance(source_doc.metadata.get('score'), float) else "")
                                st.markdown(source_doc.page_content[:500] + "...") # Visa början av texten
                        else:
                            st.markdown(f"**📄 Källa: {source_name}**")
                            st.markdown(source_doc.page_content[:500] + "...")
                        st.divider()
            # Visa SQL-fråga om den finns
            if "sql_query" in message and message["sql_query"]:
                with st.expander("Genererad SQL-fråga", expanded=False):
                    st.code(message["sql_query"], language="sql")
            # Visa SQL-resultat om det finns
            if "sql_result" in message and message["sql_result"] is not None and not message["sql_result"].empty:
                with st.expander("Databasresultat", expanded=True):
                    st.dataframe(message["sql_result"])
                    # Försök att automatiskt skapa ett diagram om det är lämpligt
                    try_render_chart(message["sql_result"])


    # --- Användarinput ---
    if prompt := st.chat_input("Ställ din fråga här... (t.ex. 'Vilka krav finns för en systemutvecklare i Stockholm?' eller 'Visa antal jobb per stad')"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # --- Agentens logik ---
        with st.chat_message("assistant"):
            response_text = "Jag kunde tyvärr inte hitta ett svar."
            rag_sources = []
            generated_sql = None
            sql_results_df = pd.DataFrame() # Initiera som tom DataFrame
            
            # Använd st.status för att visa vad som händer
            with st.status("Bearbetar din fråga...", expanded=False) as status_indicator:
                if not llm_model:
                    st.error("LLM-modellen är inte tillgänglig. Kan inte bearbeta frågan.")
                    st.session_state.messages.append({"role": "assistant", "content": "Ett internt fel uppstod (LLM ej laddad)."})
                    st.rerun()


                # 1. Bestäm intention (om funktionen finns och är konfigurerad)
                status_indicator.update(label="Analyserar din fråga...")
                try:
                    # Du behöver en bra prompt och logik för `determine_intention`
                    # För detta exempel, en förenklad logik:
                    if any(keyword in prompt.lower() for keyword in ["antal", "lista", "hur många", "vilka jobb", "visa data", "databas"]):
                        intention = "SQL_QUERY"
                    elif faiss_vector_store: # Om vector store finns, anta RAG
                        intention = "RAG_QUERY"
                    else:
                        intention = "GENERAL_CONVERSATION"
                    st.write(f"Avsikt: {intention}") # För debugging
                except Exception as e:
                    st.warning(f"Kunde inte bestämma intention: {e}. Fortsätter med RAG/Generell.")
                    intention = "RAG_QUERY" if faiss_vector_store else "GENERAL_CONVERSATION"


                # 2. Bearbeta baserat på intention
                if intention == "RAG_QUERY" and faiss_vector_store:
                    status_indicator.update(label="Söker i dokumentbasen (RAG)...")
                    try:
                        relevant_docs = get_similar_docs(faiss_vector_store, prompt, k=3)
                        if relevant_docs:
                            rag_sources = relevant_docs
                            response_text = get_llm_response_to_query_with_rag_WITHOUT_db(
                                model=llm_model,
                                query=prompt,
                                rag_context=relevant_docs
                            )
                        else:
                            status_indicator.update(label="Inga specifika dokument hittades, försöker svara generellt...")
                            response_text = get_llm_response_to_query_without_rag_or_db(llm_model, prompt)
                    except Exception as e:
                        st.error(f"Fel vid RAG-sökning: {e}")
                        response_text = "Ett fel uppstod när jag sökte i dokumenten."

                elif intention == "SQL_QUERY" and db_schema:
                    status_indicator.update(label="Försöker generera och köra SQL-fråga...")
                    try:
                        generated_sql = get_sql_from_llm(
                            model=llm_model,
                            query=prompt,
                            db_schema=db_schema
                        )
                        if generated_sql:
                            st.write(f"Genererad SQL: {generated_sql}") # Debug
                            # (Valfritt) Fråga användaren om bekräftelse innan körning
                            # if st.button("Kör SQL-fråga?"): ...
                            conn = get_db_connection()
                            if conn:
                                sql_results_df, error_msg = execute_sql_query(conn, generated_sql, return_type='dataframe')
                                conn.close()
                                if error_msg:
                                    response_text = f"Kunde inte exekvera SQL: {error_msg}. Försöker svara generellt istället."
                                    # Fallback till generell fråga om SQL misslyckas
                                    # response_text += "\n" + get_llm_response_to_query_without_rag_or_db(llm_model, prompt)
                                elif sql_results_df is not None and not sql_results_df.empty:
                                    # Försök att få LLM att summera DataFrame
                                    status_indicator.update(label="Summerar databasresultat...")
                                    summary_prompt = f"Baserat på följande data från databasen (som svar på frågan '{prompt}'), ge en kortfattad summering på svenska:\n\n{sql_results_df.to_string(index=False, max_rows=10)}\n\nSummering:"
                                    response_text = get_llm_response_to_query_without_rag_or_db(llm_model, summary_prompt)
                                    # response_text = f"Jag hittade följande data (visas nedan). {summary_llm}"
                                else:
                                    response_text = "SQL-frågan genererades och kördes, men gav inget resultat. Försöker svara generellt."
                                    # response_text += "\n" + get_llm_response_to_query_without_rag_or_db(llm_model, prompt)
                            else:
                                response_text = "Kunde inte ansluta till databasen för att köra SQL."
                        else:
                            response_text = "Kunde inte generera en SQL-fråga. Försöker svara med RAG om möjligt."
                            if faiss_vector_store:
                                relevant_docs = get_similar_docs(faiss_vector_store, prompt, k=3)
                                if relevant_docs:
                                    rag_sources = relevant_docs
                                    response_text = get_llm_response_to_query_with_rag_WITHOUT_db(llm_model, prompt, relevant_docs)
                                else:
                                    response_text = get_llm_response_to_query_without_rag_or_db(llm_model, prompt)
                            else:
                                response_text = get_llm_response_to_query_without_rag_or_db(llm_model, prompt)

                    except Exception as e:
                        st.error(f"Fel vid SQL-hantering: {e}")
                        response_text = "Ett fel uppstod när jag försökte interagera med databasen."

                else: # GENERAL_CONVERSATION eller fallback
                    status_indicator.update(label="Genererar ett allmänt svar...")
                    try:
                        response_text = get_llm_response_to_query_without_rag_or_db(llm_model, prompt)
                    except Exception as e:
                        st.error(f"Fel vid generering av allmänt svar: {e}")
                        response_text = "Ett fel uppstod när jag försökte generera ett svar."
                
                status_indicator.update(label="Färdig!", state="complete", expanded=False)

            # Visa svaret och eventuell extra information
            st.markdown(response_text)
            if rag_sources:
                with st.expander("Visade källor (RAG)", expanded=False):
                    for i, source_doc in enumerate(rag_sources):
                        source_name = source_doc.metadata.get("source", f"Källa {i+1}")
                        if shadcn_available:
                             with card(key=f"source_card_main_{i}"):
                                st.subheader(f"📄 {source_name}")
                                st.caption(f"Relevans: {source_doc.metadata.get('score', 'N/A'):.2f}" if isinstance(source_doc.metadata.get('score'), float) else "")
                                st.markdown(source_doc.page_content[:500] + "...")
                        else:
                            st.markdown(f"**📄 Källa: {source_name}**")
                            st.markdown(source_doc.page_content[:500] + "...")
                        st.divider()

            if generated_sql:
                with st.expander("Genererad SQL-fråga", expanded=False):
                    st.code(generated_sql, language="sql")
            if sql_results_df is not None and not sql_results_df.empty:
                with st.expander("Databasresultat", expanded=True):
                    st.dataframe(sql_results_df)
                    try_render_chart(sql_results_df)


            # Spara assistentens svar i historiken
            assistant_message = {"role": "assistant", "content": response_text}
            if rag_sources:
                assistant_message["sources"] = rag_sources
            if generated_sql:
                assistant_message["sql_query"] = generated_sql
            if sql_results_df is not None and not sql_results_df.empty:
                 assistant_message["sql_result"] = sql_results_df
            st.session_state.messages.append(assistant_message)
            # st.rerun() # Kan behövas för att uppdatera UI direkt, men kan också leda till dubbla körningar. Testa.

def try_render_chart(df: pd.DataFrame):
    """
    Försöker rendera ett Plotly-diagram om DataFrame är lämplig.
    """
    if df.empty or len(df.columns) < 2:
        return

    # Förenklad logik: försök skapa ett stapeldiagram om första kolumnen är kategorisk och andra numerisk
    try:
        # Försök identifiera en kategorisk och en numerisk kolumn
        cat_col = None
        num_col = None

        for col in df.columns:
            if df[col].dtype == 'object' or pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
                if df[col].nunique() < len(df): # Heuristik för kategorisk
                    cat_col = col
                    break
        
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]) and col != cat_col:
                num_col = col
                break
        
        if cat_col and num_col:
            # Sortera för bättre visualisering
            df_sorted = df.sort_values(by=num_col, ascending=False).head(15) # Visa topp 15
            
            # Använd Plotly Express för enkelhet
            import plotly.express as px
            fig = px.bar(df_sorted, x=cat_col, y=num_col, title=f"{num_col} per {cat_col}",
                         color=cat_col, template="plotly_white")
            fig.update_layout(xaxis_title=cat_col, yaxis_title=num_col, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Visualisering av de 15 främsta resultaten för '{num_col}' per '{cat_col}'.")

    except Exception as e:
        st.warning(f"Kunde inte automatiskt skapa ett diagram: {e}")


# --- Kör dashboarden ---
if __name__ == "__main__":
    # Denna del körs när du kör `python din_fil.py`
    # Om du kör via `streamlit run din_fil.py`, så kommer Streamlit att hantera det.
    # `job_agent_dashboard()` kommer att anropas av Streamlit.
    # För att denna sida ska fungera med `st_pages` i din `Start.py`,
    # behöver `Start.py` peka på denna fil och funktionen `job_agent_dashboard`.
    # Om `Start.py` bara listar .py-filer i en mapp, se till att denna fil
    # inte har en `if __name__ == "__main__": job_agent_dashboard()` som stör.
    # Streamlit kör hela skriptet från topp till botten.

    # Om du vill att denna fil ska vara den som körs direkt med `streamlit run gemini.py`
    job_agent_dashboard()