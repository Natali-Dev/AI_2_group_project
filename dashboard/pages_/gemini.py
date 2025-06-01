import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"INFO : Lade till {PROJECT_ROOT} i sys.path")

try:
    from definitions import DB_PATH, EMBEDDING_DIM, EMBEDDINGS_DB_PATH # Lade till EMBEDDINGS_DB_PATH
except ImportError:
    st.error("VIKTIGT: Kunde inte importera DB_PATH, EMBEDDING_DIM och/eller EMBEDDINGS_DB_PATH från definitions.py! Kontrollera filen.")
    DB_PATH = None 
    EMBEDDING_DIM = 384 
    EMBEDDINGS_DB_PATH = None # Lägg till fallback
    if not DB_PATH or not EMBEDDINGS_DB_PATH: 
        st.stop()

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Importera moduler med korrekta funktionsnamn
from llm_core.interaction import (
    configure_gemini,
    get_gemini_model,
    determine_user_intention,
    answer_question_with_rag,
    generate_sql_from_question,
    get_general_llm_response,
    summarize_dataframe_with_llm
    # get_qualities_from_gemini
)

from llm_core.utility import get_db_connection
from llm_core.db_executor import execute_sql_query
from llm_core.schema_provider import get_schema_representation
from rag_pipeline.duckdb_vss_utils import get_similar_docs_duckdb
#from rag_pipeline.setup_embedding_db import (
#   load_vector_store,
#   get_similar_docs
#)

try:
    from definitions import DB_PATH, EMBEDDING_DIM # Importera båda
except ImportError:
    st.error("VIKTIGT: Kunde inte importera DB_PATH och/eller EMBEDDING_DIM från definitions.py! Kontrollera filen.")
    DB_PATH = None 
    EMBEDDING_DIM = 384 # Sätt ett standardvärde om det saknas
    if not DB_PATH: # Om DB_PATH inte kunde sättas, är det kritiskt.
        st.stop()

# För moderna UI-komponenter
try:
    from streamlit_shadcn_ui import card # Importera bara det du använder
    shadcn_available = True
except ImportError:
    shadcn_available = False
    # st.warning("streamlit-shadcn-ui är inte installerad.") # Kan vara tystare

load_dotenv()

if not configure_gemini():
    st.error("FATALT FEL: Kunde inte konfigurera Gemini API.")
    st.stop()

# --- Konfiguration och Initialisering (cachas) ---
# @st.cache_resource # Viktigt för prestanda
def initialize_agent_components():
    print("DEBUG (gemini.py - initialize_agent_components): Startar funktionen.") # NY PRINT
    
    model = get_gemini_model() # Använder funktionen från interaction.py
    if model is None:
        st.error("Kunde inte ladda Gemini-modellen från llm_core.interaction.")
        print("DEBUG (gemini.py - initialize_agent_components): Gemini-modell kunde INTE laddas.") # NY PRINT
        return None, None 
    print("DEBUG (gemini.py - initialize_agent_components): Gemini-modell laddad.") # NY PRINT

    db_schema_info = None
    print(f"DEBUG (gemini.py - initialize_agent_components): DB_PATH från definitions: {DB_PATH}") # NY PRINT
    
    if DB_PATH and os.path.exists(DB_PATH): # Kontrollerar att DB_PATH är giltig
        print(f"DEBUG (gemini.py - initialize_agent_components): DB_PATH '{DB_PATH}' existerar.") # NY PRINT
        conn = None 
        try:
            print("DEBUG (gemini.py - initialize_agent_components): Försöker ansluta till DB...") # NY PRINT
            conn = get_db_connection(db_path=DB_PATH, read_only=True) 
            if conn:
                print("DEBUG (gemini.py - initialize_agent_components): Anslutning till DB lyckades. Försöker hämta schema...") # NY PRINT
                db_schema_info = get_schema_representation(
                    db_connection=conn, 
                    schemas_to_include=['mart', 'refined'], # Specificerar scheman
                    format_for_llm=True
                )
                print(f"DEBUG (gemini.py - initialize_agent_components): db_schema_info från get_schema_representation: {db_schema_info[:200] if db_schema_info else 'None'}") # NY PRINT (visar början)
                if not db_schema_info:
                     st.warning("Kunde inte hämta databasschemat från DuckDB (mart, refined). Kontrollera att dbt har körts och att tabeller finns i dessa scheman.")
            else:
                st.warning("Kunde inte ansluta till DuckDB för att hämta schema (get_db_connection returnerade None).")
                print("DEBUG (gemini.py - initialize_agent_components): get_db_connection returnerade None.") # NY PRINT
        except Exception as e:
            st.error(f"Fel vid hämtning av databasschema (DuckDB) i initialize_agent_components: {e}")
            print(f"DEBUG (gemini.py - initialize_agent_components): Exception vid DB-anslutning/schemahämtning: {e}") # NY PRINT
            import traceback
            traceback.print_exc() # Skriver ut hela stacktrace för detta fel
        finally:
            if conn:
                conn.close()
                print("DEBUG (gemini.py - initialize_agent_components): DB-anslutning stängd.") # NY PRINT
    elif not DB_PATH:
        st.warning("DB_PATH är inte definierad (från definitions.py). Kan inte hämta schema.")
        print("DEBUG (gemini.py - initialize_agent_components): DB_PATH är inte definierad.") # NY PRINT
    elif not os.path.exists(DB_PATH): 
        st.error(f"DB_PATH är '{DB_PATH}', men filen hittades inte. Kontrollera att dbt/dlt pipeline har körts och att sökvägen i definitions.py är korrekt.")
        print(f"DEBUG (gemini.py - initialize_agent_components): Filen för DB_PATH ('{DB_PATH}') hittades inte.") # NY PRINT
    
    print(f"DEBUG (gemini.py - initialize_agent_components): Returnerar model och db_schema_info: {'Schema finns' if db_schema_info else 'Schema är None'}") # NY PRINT
    return model, db_schema_info

# Ladda komponenter
llm_model, db_schema = initialize_agent_components()

if llm_model is None: # Kontrollera om modellen laddades korrekt
    st.error("LLM-modellen kunde inte initieras. Applikationen kan inte fortsätta.")
    st.stop()

# --- Huvudfunktion för JobbAgenten Dashboard ---
def job_agent_dashboard(df=None, field=None):
    if shadcn_available:
        cols = st.columns([0.8, 0.2])
        with cols[0]:
            st.title("🤖 JobbAgenten Deluxe")
            st.caption("Din intelligenta assistent för att utforska jobbannonser och datainsikter.")
        with cols[1]:
            # Använd en unik nyckel för knappen om du har flera på sidan
            if st.button("Rensa chatt", type="secondary", key="clear_chat_main_button"):
                 st.session_state.messages = []
                 st.rerun()
    else:
        st.title("🤖 JobbAgenten Deluxe")
        st.caption("Din intelligenta assistent för att utforska jobbannonser och datainsikter.")
        if st.button("Rensa chatt", key="clear_chat_main_button_no_shadcn"):
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hej! Hur kan jag hjälpa dig att utforska jobbannonser idag?"}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("Visade källor (RAG)", expanded=False):
                    for i, source_doc in enumerate(message["sources"]):
                        source_name = source_doc.metadata.get("source", f"Källa {i+1}") if hasattr(source_doc, 'metadata') else f"Källa {i+1}"
                        page_content_display = source_doc.page_content if hasattr(source_doc, 'page_content') else str(source_doc)

                        if shadcn_available:
                            # Generera en unik nyckel för varje kort
                            card_key = f"source_card_{message['role']}_{st.session_state.messages.index(message)}_{i}"
                            with card(key=card_key):
                                st.subheader(f"📄 {source_name}")
                                if hasattr(source_doc, 'metadata') and isinstance(source_doc.metadata.get('score'), float):
                                    st.caption(f"Relevans: {source_doc.metadata.get('score'):.2f}")
                                st.markdown(page_content_display[:500] + "...")
                        else:
                            st.markdown(f"**📄 Källa: {source_name}**")
                            st.markdown(page_content_display[:500] + "...")
                        if i < len(message["sources"]) - 1: st.divider()
            if "sql_query" in message and message["sql_query"]:
                with st.expander("Genererad SQL-fråga", expanded=False):
                    st.code(message["sql_query"], language="sql")
            if "sql_result" in message and isinstance(message["sql_result"], pd.DataFrame) and not message["sql_result"].empty:
                with st.expander("Databasresultat", expanded=True):
                    st.dataframe(message["sql_result"])
                    try_render_chart(message["sql_result"])


    if prompt := st.chat_input("Ställ din fråga här..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response_text = "Jag kunde tyvärr inte hitta ett svar."
            rag_sources = []
            generated_sql = None
            sql_results_df = pd.DataFrame()
            
            with st.status("Bearbetar din fråga...", expanded=False) as status_indicator:
                if not llm_model: # llm_model är nu den globala från initialize_agent_components
                    st.error("LLM-modellen är inte tillgänglig.")
                    st.session_state.messages.append({"role": "assistant", "content": "Internt fel: LLM ej laddad."})
                    st.rerun()

                status_indicator.update(label="Analyserar din fråga...")
                intention = determine_user_intention(prompt, db_schema=db_schema) # Skicka med db_schema
                st.write(f"DEBUG: Avsikt: {intention}")

                if intention == "RAG_QUERY" and EMBEDDINGS_DB_PATH and os.path.exists(EMBEDDINGS_DB_PATH) and EMBEDDING_DIM:
                    status_indicator.update(label="Söker i dokumentbasen (RAG)...")
                    try:
                        relevant_docs = get_similar_docs_duckdb(
                            db_path=EMBEDDINGS_DB_PATH,  # Använd EMBEDDINGS_DB_PATH här!
                            query_text=prompt,
                            k=3, 
                            embedding_dim=EMBEDDING_DIM
                        )
                        if relevant_docs:
                            rag_sources = relevant_docs
                            
                            response_text = answer_question_with_rag(
                                question=prompt,
                                context_chunks=relevant_docs # answer_question_with_rag hanterar Document-objekt
                            )
                        else:
                            status_indicator.update(label="Inga specifika dokument hittades, svarar generellt...")
                            
                            response_text = get_general_llm_response(prompt)
                    except Exception as e:
                        st.error(f"Fel vid RAG-sökning: {e}")
                        response_text = "Ett fel uppstod när jag sökte i dokumenten."

                elif intention == "SQL_QUERY" and db_schema:
                    status_indicator.update(label="Genererar och kör SQL-fråga...")
                    try:
                        
                        generated_sql = generate_sql_from_question(
                            natural_language_question=prompt,
                            db_schema_description=db_schema
                        )
                        if generated_sql and "SELECT 'Informationen kan inte hämtas" not in generated_sql and "FEL:" not in generated_sql.upper() :
                            st.write(f"DEBUG: Genererad SQL: {generated_sql}")
                            conn = get_db_connection(db_path=DB_PATH, read_only=True)
                            if conn:
                                sql_results_df, error_msg = execute_sql_query(db_connection=conn, sql_query=generated_sql, return_type='dataframe')
                                # conn.close() # Stängs i execute_sql_query om den skapades där
                                if error_msg:
                                    response_text = f"Kunde inte exekvera SQL: {error_msg}."

                                elif sql_results_df is not None and not sql_results_df.empty:
                                    status_indicator.update(label="Summerar databasresultat...")
                                    response_text = summarize_dataframe_with_llm(sql_results_df, prompt)
                                else: # SQL kördes men gav tomt resultat
                                    response_text = "SQL-frågan kördes men gav inget data tillbaka. Det kan betyda att det inte finns någon matchande data, eller så behöver frågan justeras."
                            else:
                                response_text = "Kunde inte ansluta till databasen för att köra SQL."
                        elif generated_sql and ("SELECT 'Informationen kan inte hämtas" in generated_sql or "FEL:" in generated_sql.upper()):
                            response_text = f"Jag kunde inte skapa en SQL-fråga för detta, eller så finns informationen inte i databasen. LLM sa: '{generated_sql.split('SELECT')[-1].strip()[:-2]}'" # Visa LLM-felet
                            generated_sql = None # Nollställ om det var ett "fel"-select
                        else: # Ingen SQL genererades alls
                            response_text = "Jag kunde inte omvandla din fråga till en SQL-fråga. Försöker svara generellt."
                            response_text = get_general_llm_response(prompt)


                    except Exception as e:
                        st.error(f"Fel vid SQL-hantering: {e}")
                        response_text = "Ett oväntat fel uppstod när jag försökte interagera med databasen."

                else: # GENERAL_CONVERSATION eller fallback om RAG/SQL inte är tillämpligt/möjligt
                    status_indicator.update(label="Genererar ett allmänt svar...")
                    
                    response_text = get_general_llm_response(prompt)
                
                status_indicator.update(label="Färdig!", state="complete", expanded=False)
            
            st.markdown(response_text if response_text else "Jag har inget svar just nu.") # Se till att response_text alltid har ett värde

            assistant_message = {"role": "assistant", "content": response_text if response_text else "Jag har inget svar just nu."}
            if rag_sources:
                assistant_message["sources"] = rag_sources
            if generated_sql:
                assistant_message["sql_query"] = generated_sql
            if sql_results_df is not None and not sql_results_df.empty:
                 assistant_message["sql_result"] = sql_results_df
            st.session_state.messages.append(assistant_message)
            # st.rerun() # Oftast inte nödvändigt, Streamlit uppdaterar reaktivt

def try_render_chart(df: pd.DataFrame):
    if df is None or df.empty or len(df.columns) < 1: # Ändrat till < 1, om bara en kolumn kan det vara en lista av värden
        return
    try:
        # ... (din try_render_chart-logik, se till att den importerar plotly.express lokalt) ...
        import plotly.express as px # Importera här för att hålla det lokalt
        # Förenklad logik: försök skapa ett stapeldiagram om första kolumnen är kategorisk och andra numerisk
        # Eller om det bara finns en numerisk kolumn, kanske ett histogram?
        # Eller om det finns två numeriska kolumner, ett punktdiagram?
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        string_cols = df.select_dtypes(include=['object', 'string', 'category']).columns.tolist()

        chart_title = "Visualisering av data"
        fig = None

        if len(numeric_cols) == 1 and len(string_cols) >= 1:
            # Troligen stapeldiagram: string_cols[0] som x, numeric_cols[0] som y
            cat_col = string_cols[0]
            num_col = numeric_cols[0]
            if df[cat_col].nunique() < len(df) and df[cat_col].nunique() > 1 : # Se till att det är en vettig kategorisk axel
                df_sorted = df.sort_values(by=num_col, ascending=False).head(20) # Visa topp 20
                fig = px.bar(df_sorted, x=cat_col, y=num_col, title=f"{num_col} per {cat_col}", color=cat_col)
                chart_title = f"{num_col} per {cat_col}"
        elif len(numeric_cols) >= 2:
            # Kanske ett punktdiagram om det finns en tydlig relation, eller flera linjer om det finns en tidsaxel
            # För enkelhet, ta de två första numeriska
            fig = px.scatter(df.head(100), x=numeric_cols[0], y=numeric_cols[1], title=f"{numeric_cols[1]} vs {numeric_cols[0]}", trendline="ols" if len(df) > 1 else None)
            chart_title = f"{numeric_cols[1]} vs {numeric_cols[0]}"
        elif len(numeric_cols) == 1:
            fig = px.histogram(df, x=numeric_cols[0], title=f"Distribution av {numeric_cols[0]}")
            chart_title = f"Distribution av {numeric_cols[0]}"

        if fig:
            fig.update_layout(showlegend=False, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            st.caption(chart_title)

    except ImportError:
        st.warning("Plotly Express är inte installerat. Kan inte rendera diagram.")
    except Exception as e:
        st.warning(f"Kunde inte automatiskt skapa ett diagram: {e}")


if __name__ == "__main__":
    job_agent_dashboard()