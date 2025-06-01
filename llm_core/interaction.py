import re
import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

from .schema_provider import get_schema_representation

# Globala variabler för modellerna och konfigurationsstatus
gemini_model_standard = None # För RAG, summeringar, generell, chat
gemini_model_text_to_sql: None # Kan vara samma som standard, eller finjusterad modell
gemini_api_key_configured = False

SUPPORTED_INTENTIONS = ["SQL_QUERY", "RAG_QUERY", "GENERAL_CONVERSATION"]

def configure_gemini():
    """
    Konfigurerar Gemini API'n. Försöker först med st.secrets, sedan miljövariabler.
    Returnerar True om konfiguratonen lyckades, annard False.
    Initierar gemini_model_standard och gemini_model_text_to_sql.
    """

    global gemini_model_standard, gemini_model_text_to_sql, gemini_api_key_configured

    if gemini_api_key_configured:
        print("INFO (interaction.py): Gemini API redan konfiguerad.")
        return True
    api_key = None
    try:
        # Försök hämta streamlit secrets om tillgängligt
        if hasattr(st, 'secrets') and "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
            api_key = st.secrets["GEMINI_API_KEY"]
            print("INFO (interaction.py): GEMINI_API_KEY hittades i st.secrets.")
    except Exception:
        pass # Ignorerra fel om st.secrets inte är tillgängligt (t.ex. vid körning utanför Streamlit)

    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            print("INFO (interaction.py): GEMINI_API_KEY hittades i miljövariabler.")

    if not api_key:
        error_message = "VARNING (interaction.py): GEMINI_API_KEY hittades inte i st.secrets eller miljövariabler."
        print (error_message)
        if hasattr(st,'error'): #Visa fel i Streamlit UI om möjligt
            st.error("API-nyckel för Gemini inte konfiguerad. Kontrollera din secrets.toml eller miljövariablen GEMINI_API_KEY.")
        gemini_api_key_configured = False
        return False
    
    try:
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL_NAME", 'gemini-1.5-flash-latest') # Tillåt override via miljövariabel

        gemini_model_standard = genai.GenerativeModel(model_name)
        gemini_model_text_to_sql = genai.GenerativeModel(model_name)

        gemini_api_key_configured = True
        print(f"INFO (interaction.py): Gemini API konfiguerad. Modell: {model_name} har initierats.")
        return True
    except Exception as e:
        error_message = f"FEL (interaction.py): Ett fel inträäffade vid konfiguering av Gemini API'n: {e}"
        print(error_message)
        if hasattr(st,'error'):
            st.error(error_message)
        gemini_api_key_configured = False
        return False
    
def get_gemini_model(model_type="standard"): # Helper för dashboarden
    """Returnerar en initierad Gemini-modell."""
    global gemini_model_standard, gemini_model_text_to_sql, gemini_api_key_configured

    if not gemini_api_key_configured:
        # Försök konfigurera om det inte redan är gjort eller om ingen modell är satt
        if not configure_gemini():
            print("FEL (interaction.py -> get_gemini_model): Kunde inte konfigurera Gemini.")
            return None
            
    if model_type == "text_to_sql" and gemini_model_text_to_sql:
        return gemini_model_text_to_sql
    elif model_type == "standard" and gemini_model_standard: # 'standard' kan användas för RAG, summering etc.
        return gemini_model_standard
    elif gemini_model_standard: # Fallback till standardmodellen om typen är okänd men standard finns
        print(f"VARNING (interaction.py -> get_gemini_model): Okänd modelltyp '{model_type}', returnerar standardmodell.")
        return gemini_model_standard
    
    print(f"FEL (interaction.py -> get_gemini_model): Ingen lämplig modell hittades för typ '{model_type}'.")
    return None


if not gemini_api_key_configured:
    print("INFO (interaction.py): Försöker konfiguera Gemini vid import...")
    configure_gemini()

def determine_user_intention(user_query: str, db_schema: str | None = None) -> str:
    """
    Bestämmer användarens avsikt baserat på frågan.
    Detta är en förenklad  version. Kan utökas med LLM-anrop för med avancerad logik.

    Args:
        user_query: Användarens fråga.
        db_schema: Databasschemat (valfritt, men kan hjälpa LLM att förstå rätt SQL-intention).

    Returns:
        En sträng som representerar intentionen (t.xe. "SQL_QUERY", "RAG_QUERY", "GENERAL_CONVERSATION").
    """
    global gemini_model_standard, gemini_api_key_configured
    query_lower = user_query.lower()

    # Nyckelord för SQL-frågor
    sql_keywords = ["antal", "lista", "hur många", "visa data", "databas", "tabell", "räkna", "summera", "genomsnitt"]
    if any(keyword in query_lower for keyword in sql_keywords):
        print(f"INFO (interaction.py -> determine_intention): Tolkad som SQL_QUERY baserat på nyckelord: {user_query}")
        return "SQL_QUERY"
    
    if gemini_model_standard and gemini_api_key_configured:
        print(f"INFO (interaction.py -> determine_intention): Tolkad som RAG_QUERY (fallback): {user_query}")
        return "RAG_QUERY" # Fallback till RAG om inte SQL och RAG-modell finns.
    
    print(f"INFO (interaction.py -> determina_intention): Tolkad som GENERAL_CONVERSATION (sista fallback): {user_query}")
    return "GENERAL_CONVERSATION"

def generate_sql_from_question(natural_language_question: str, db_schema_description: str) -> str | None:
    # Genererar en SQL fråga från en naturlig språkfråga och ett databasschema.
    
    global gemini_model_text_to_sql, gemini_api_key_configured # gemini_api_key_configured bör också kollas

    # configure_gemini() bör redan ha körts när modulen importeras,
    # men en extra kontroll här för gemini_model_text_to_sql är bra.
    if not gemini_model_text_to_sql or not gemini_api_key_configured:
        # Försök konfigurera igen om det misslyckats tidigare eller om modellen är None
        if not configure_gemini() or not gemini_model_text_to_sql:
            error_msg = "FEL (interaction.py): Gemini Text-to-SQL modell inte initierad. Kontrollera API-nyckeln."
            print(error_msg)
            if hasattr(st, 'error'): st.error(error_msg)
            # KORRIGERING: SQL-säkert felmeddelande och return
            safe_error_msg = error_msg.replace("'", "''") # Ersätt enkla citationstecken för SQL
            return f"SELECT '{safe_error_msg}';"

    prompt = f""" 
Du är en expert på att omvandla naturligt språk till DuckDB SQL-frågor.
Databasens schema är som följer:
--- SCHEMA START ---
{db_schema_description}
--- SCHEMA SLUT ---
    
Användarens fråga: "{natural_language_question}"

Din uppgift är att generera en ENKEL KÖRBAR DuckDB SQL SELECT-fråga som besvarar användarens fråga baserat på det givna schemat.
VIKTIGT:
1. Svara ENDAST med SQL-frågan. Inkludera INGA förklaringar, introduktioner, exempel, markdown-formatering (som ```sql), eller någon annan text före eller efter SQL-koden.
2. Om frågan inte kan besvaras med det givna schemat, är tvetydig eller om du är osäker, svara med EXAKT: SELECT 'Informationen kan inte hämtas med nuvarande schema och fråga.';
3. Använd dubbla citationstecken (") runt tabell- och kolumnnamn om de innehåller specialtecken, versaler eller är reserverade ord (t.ex. "main"."dim_job_details"."description"). Standard DuckDB är skiftlägesokänsligt för oquoterade identifierare, men använd quotes för säkerhets skull, särskilt om schemat indikerar det. (Liten korrigering: "skiftlägesokänsligt")
4. Försök att använda `lower()` på textkolumner i WHERE-klausuler för skiftlägesokänslig matchning där det är lämpligt och kolumnen är av texttyp.
5. Undvik att returnera för många kolumner om inte frågan specifikt ber om det. Fokusera på de mest relevanta.
6. Om frågan ber dig om en beskrivning eller fritext, och det finns en relevant textkolumn (t.ex. 'description'), returnera den.

SQL-fråga:
"""

    try:
        # print("\n--- Skickar följande prompt till Gemini för SQL-generering ---") # Kan vara för mycket loggning
        # print(f"FRÅGA: {natural_language_question}")
        # print("---------------------------------------------------------------\n")

        response = gemini_model_text_to_sql.generate_content(prompt)
        generated_sql_raw = ""
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            generated_sql_raw = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
        elif hasattr(response, 'text') and response.text:
            generated_sql_raw = response.text
        else:
            print(f"VARNING (interaction.py): Inget textinnehåll i svaret från Gemini för SQL-generering. Svar: {response}") # Korrigerad typo: VARNINING -> VARNING
            return "SELECT 'Internt fel: Tomt svar från LLM vid SQL-generering.';" # Korrigerad: Tog bort extra punkt.

        generated_sql = generated_sql_raw.strip()
        generated_sql = re.sub(r"^\s*```sql\s*", "", generated_sql, flags=re.IGNORECASE)            
        generated_sql = re.sub(r"\s*```\s*$", "", generated_sql)
        generated_sql = generated_sql.strip("`") if not (generated_sql.startswith("`\"") or generated_sql.endswith("\"`")) else generated_sql
        generated_sql = generated_sql.strip()

        # print(f"DEBUG (interaction.py): Rått svar från Gemini (SQL): '{generated_sql_raw}'") # Bra för debugging
        print(f"DEBUG (interaction.py): Rensad SQL från Gemini: '{generated_sql}'") # Korrigerad typo: DEBIG -> DEBUG

        if not generated_sql:
            print("VARNING (interaction.py): Genererad SQL är tom efter rensning.")
            return "SELECT 'Internt fel: Tom SQL genererad efter rensning.';"

        if not generated_sql.upper().startswith("SELECT"):
            print(f"VARNING (interaction.py): Genererad SQL är inte en SELECT-sats: '{generated_sql}'")
            match = re.search(r"(SELECT\s+[^;]+;?)", generated_sql, re.IGNORECASE | re.DOTALL) # Lite mer restriktiv regex
            if match:
                generated_sql = match.group(1).strip()
                print(f"DEBUG (interaction.py): Extraherad SELECT från pratigt svar: '{generated_sql}'")
                # Dubbelkolla att den extraherade faktiskt är en SELECT
                if not generated_sql.upper().startswith("SELECT"):
                    error_payload = f"Ogiltig SQL (ej SELECT efter extrahering): {generated_sql_raw[:100]}".replace("'", "''")
                    return f"SELECT '{error_payload}';"
            else:
                error_payload = f"Ogiltig SQL genererad (inte en SELECT): {generated_sql_raw[:100]}".replace("'", "''")
                return f"SELECT '{error_payload}';"
        
        return generated_sql
    except Exception as e:
        error_msg_text = f"Fel (interaction.py) vid generering av SQL från Gemini: {e}" # Korrigerad typo: genereing -> generering
        print(error_msg_text)
        if hasattr(st, 'error'): st.error(error_msg_text)
        exception_payload = f"Tekniskt fel vid SQL-generering: {str(e)}".replace("'", "''")
        return f"SELECT '{exception_payload}';"


def answer_question_with_rag(question: str, context_chunks: list[str]) -> str | None:
    #Svarar på en fråga baserat på RAG-kontext.
    global gemini_model_standard, gemini_api_key_configured

    if not configure_gemini() or not gemini_model_standard:
        error_msg = "FEL (interaction.py): Gemini RAG-modell inte initierad. Kontrollera API-nyckeln."
        print(error_msg)
        if hasattr(st, 'error'): st.error(error_msg)
        return "LLM-modell för RAG är inte tillgänglig."
        
    if not context_chunks:
        print("INFO (interaction.py -> answer_question_with_rag): Ingen kontext given för RAG.")
        #return "Jag kunde inte hitta tillräckligt med relevant information i jobbannonserna för att svara på din fråga."
        return get_general_llm_response(question)


    context_string = "\n---\n".join(chunk.page_content if hasattr(chunk, 'page_content') else str(chunk) for chunk in context_chunks)
    
    prompt = f"""Du är en AI-assistent specialiserad på att analysera jobbannonser.
Svara på användarens fråga ENDAST baserat på följande kontext från jobbannonser. Använd ingen extern kunskap.
Om svaret inte tydligt framgår av kontexten, ange att informationen inte finns i den tillhandahållna texten eller försök att ge det bästa möjliga svaret baserat på fragment om det är allt som finns.
Var koncis och direkt i ditt svar. Strukturera svaret läsbart, använd punktlistor om det är lämpligt.

Kontext från jobbannonser:
---
{context_string}
---
Användarens fråga: {question}

Svar:"""

    try:
        print(f"\n--- Skickar följande prompt till Gemini för RAG-svar ---")
        print(f"FRÅGA: {question}")
        # print(f"KONTEXT (början): \n{context_string[:500]}") # Kan vara mycket data
        print("--------------------------------------------------------\n")

        response = gemini_model_standard.generate_content(prompt)
        answer = response.text.strip() if hasattr(response, 'text') and response.text else ""
        if not answer and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
             answer = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')).strip()


        print(f"DEBUG (interaction.py): Svar från Gemini (RAG): {answer}")
        if not answer:
            return "Jag fick ett tomt svar från modellen. Försök igen."
        return answer
    except Exception as e:
        error_msg = f"Fel (interaction.py) vid generering av RAG-svar från Gemini: {e}"
        print(error_msg)
        if hasattr(st, 'error'): st.error(error_msg)
        return "Ett tekniskt fel uppstod när jag försökte generera ett svar."

def get_general_llm_response(query: str) -> str:
    """Hämtar ett generellt svar från LLM utan specifik RAG-kontext eller SQL."""
    global gemini_model_standard, gemini_api_key_configured
    if not configure_gemini() or not gemini_model_standard:
        return "LLM-modell är inte tillgänglig."
    
    prompt = f"""Du är en hjälpsam AI-assistent. Svara på följande fråga eller instruktion:
    {query}
    """
    try:
        response = gemini_model_standard.generate_content(prompt)
        answer = response.text.strip() if hasattr(response, 'text') and response.text else ""
        if not answer and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
             answer = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')).strip()
        return answer if answer else "Jag kunde inte generera ett svar."
    except Exception as e:
        print(f"FEL (interaction.py -> get_general_llm_response): {e}")
        return "Ett fel uppstod när jag försökte kommunicera med LLM."


def summarize_dataframe_with_llm(dataframe: pd.DataFrame, user_question: str) -> str | None:
    """Summerar innehållet i en Pandas DataFrame med hjälp av LLM, i kontexten av användarens fråga."""
    global gemini_model_standard, gemini_api_key_configured

    if not configure_gemini() or not gemini_model_standard:
        error_msg = "FEL (interaction.py): Gemini-modell för summering inte initierad."
        print(error_msg)
        if hasattr(st, 'error'): st.error(error_msg)
        return "LLM-modell för summering är inte tillgänglig."

    if dataframe.empty:
        return "Det fanns ingen data att summera."

    # Konvertera DataFrame till en läsbar strängrepresentation (t.ex. markdown eller CSV-liknande)
    # Begränsa mängden data som skickas till LLM:en för att undvika token-limits
    sample_data_str = dataframe.head(15).to_markdown(index=False) # Skicka de första 15 raderna som markdown

    prompt = f"""Baserat på användarens fråga: "{user_question}"
Och följande data som hämtats från databasen:
--- DATA START ---
{sample_data_str}
--- DATA SLUT ---
(Notera: Detta kan vara ett utdrag av den fullständiga datan. Totalt antal rader i datasetet är {len(dataframe)}.)

Ge en koncis och informativ summering av datan på svenska som svarar på användarens fråga.
Fokusera på de viktigaste insikterna. Om datan är en lista, sammanfatta vad listan innehåller.
Om det är numerisk data, nämn eventuella trender eller nyckeltal.
Svara direkt på frågan med hjälp av summeringen.
"""
    try:
        print(f"\n--- Skickar prompt till Gemini för DataFrame-summering ---")
        # print(f"DATA (utdrag): \n{sample_data_str}")
        print("----------------------------------------------------------\n")
        response = gemini_model_standard.generate_content(prompt)
        summary = response.text.strip() if hasattr(response, 'text') and response.text else ""
        if not summary and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
             summary = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')).strip()

        print(f"DEBUG (interaction.py): Summering från Gemini: {summary}")
        return summary if summary else "Kunde inte generera en summering av datan."
    except Exception as e:
        error_msg = f"Fel (interaction.py) vid summering av DataFrame från Gemini: {e}"
        print(error_msg)
        if hasattr(st, 'error'): st.error(error_msg)
        return "Ett tekniskt fel uppstod när jag försökte summera datan."

def get_qualities_from_gemini(job_descriptions_text: str, occupation_field: str) -> str | None:
    """ 
    Analyserar jobbannonsbeskrivningar med Gemini för att identifiera nyckelkvalifikationer.
    Använder den globalt konfigurerade gemini_model_standard.
    """
    global gemini_model_standard, gemini_api_key_configured
    
    if not configure_gemini() or not gemini_model_standard:
        error_msg = "FEL (interaction.py): Gemini-modell (standard) inte initierad för get_qualities."
        print(error_msg)
        if hasattr(st, 'error'): st.error(error_msg)
        return None
        
    prompt = f"""
    Analysera följande jobbannonsbeskrivningar för yrkesområdet '{occupation_field}':
    ---JOBBANNONSBESKRIVNINGAR---
    {job_descriptions_text[:10000]} 
    ---SLUT PÅ BESKRIVNINGAR---
    Baserat på texten ovan, identifiera och lista de 5-7 viktigaste och mest återkommande önskvärda kvalifikationerna, 
    färdigheterna eller egenskaperna som arbetsgivare söker.
    Presentera dem som en tydlig, kommaseparerad lista. Undvik onödiga inledningsfraser.
    Exempel på output: "Kommunikativ, Problemlösare, Lagspelare, Erfarenhet av Python, Projektledning"
    """
    try:
        print(f"INFO (interaction.py): Skickar prompt till Gemini (get_qualities) för yrkesområde: {occupation_field}")
        response = gemini_model_standard.generate_content(prompt) # Använder standardmodellen

        extracted_text = ""
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            extracted_text = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')).strip()
        elif hasattr(response, 'text') and response.text:
            extracted_text = response.text.strip()

        if extracted_text:
            print(f"INFO (interaction.py): Mottaget svar från Gemini (get_qualities): {extracted_text}")
            return extracted_text
        else:
            print("VARNING (interaction.py): Tom text extraherad från Gemini-svarets delar (get_qualities).")
            if hasattr(st, 'warning'): st.warning("Modellen returnerade ett svar men det var tomt (get_qualities).")
            return None
            
    except Exception as e:
        error_msg = f"FEL (interaction.py): Fel vid anrop till Gemini (get_qualities): {e}"
        print(error_msg)
        # Specifik felhantering från din ursprungliga kod
        if "API key not valid" in str(e):
            if hasattr(st, 'error'): st.error("API-nyckel för Gemini är inte giltig. Kontrollera att den är korrekt inlagd.")
        elif "quota" in str(e).lower():
            if hasattr(st, 'error'): st.error("API-kvoten för Gemini har troligen överskridits. Vänta och försök igen senare.")
        else:
            if hasattr(st, 'error'): st.error("Ett internt fel uppstod vid anrop till Gemini (get_qualities).")
        return None
