
# För att detta ska funka så måste du lägga in din api nyckel i mappen ".streamlit och sedan i filen "secrets.toml".

import streamlit as st
import google.generativeai as genai
import os


gemini_model_text_to_sql = None
gemini_model_rag = None
gemini_api_key_configured = False


def configure_gemini():
    """
    Konfigurerar Gemini API'n. Försöker först med st.secrets, sedan miljövariabler.
    Retunerar True om konfigurationen lyckades, annars False.
    Initierar gemini_model_text_to_sql och gemini_model_rag.
    """
    global gemini_model_text_to_sql, gemini_model_rag, gemini_api_key_configured
    
    if gemini_api_key_configured:
        print("INFO: Gemini API redan konfigurerad.")
        return True
    
    api_key = None
    try:
        if hasattr(st, 'secrets') and "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
            api_key = st.secrets["GEMINI_API_KEY"]
            print("INFO: GEMINI_API_KEY hittades i st.secrets.")
    except Exception:
        pass
    
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            print("INFO: GEMINI_API_KEY hittades i miljövariabler.")
        else:
            print("VARNING: GEMINI_API_KEY hittades inte i st.secrets eller miljövariabler.")
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model_name = 'gemini-1.5-flash-latest'
            gemini_model_text_to_sql = genai.GenerativeModel(model_name)
            gemini_model_rag = genai.GenerativeModel(model_name)
            gemini_api_key_configured = True
            print(f"INFO: Gemini API konfigurerad. Modell: {model_name} har iniatiserats.")
            return True
        except Exception as e:
            print(f"FEL: Ett fel inträffade vid konfiguering av Gemini APIn: {e}")
            if hasattr(st, 'error'):
                st.error(f"Ett fel inträffade vid konfiguering av Gemini APIn: {e}")
            gemini_api_key_configured = False
            return False
    else:
        if hasattr(st, 'error'):
            st.error("API.nyckel för Gemini är inte konfiguerad. Kontrollera st.secrets eller miljövariabeln GEMINI_API_KEY.")
        gemini_api_key_configured = False
        return False


if not gemini_api_key_configured:
        print("INFO: Försöker konfiguear Gemini vid import av interaction.py...")
        configure_gemini()

def generate_sql_from_question(natural_language_question: str, db_schema_description: str) -> str | None:
    global gemini_model_text_to_sql, gemini_api_key_configured

    if not gemini_api_key_configured or gemini_model_text_to_sql is None:
        error_msg = "FEL: Gemini Text-to-SQL modell inte initierad. Kör configure_gemini() först. eller kontrollera API-nyckeln."
        print(error_msg)
        if hasattr(st, 'error'): st.error(error_msg)
        return "SELECt 'FEL: Gemini Text-to-SQL modell inte initierad'"
    prompt = f"""{db_schema_description}

Användarens fråga: "{natural_language_question}"

Baserat på schemat och användarens fråga, generera en enda körbar DuckDB SQL SELECT-fråga.
Svara ENDAST med SQL-frågan. Inkludera inga förklaringar, introduktioner, markdown-formatering (som ```sql) eller extra text för eller efter SQL-koden.
Om frågan inte kan besvaras med det givna schemat, eller om den är tvetydlig, svara med exakt: SELECT 'Informationen kan inte hämtas med nuvarande schema och fråga.';
Använd citationstecken (") runt tabell- och kolumnnamn om de innehåller specialtecken, versaler eller är reserverade ord (t.ex "refined"."dim_job_details"."id").
Försök att använda 'lower()' på textkolumner i WHERE-klausuler för skiftlägesokänslig matchning om det verkar lämpligt och kolumen är av texttyp.
"""
    try:
        print(f"\n--- Skickar följande prompt till Gemini för SQL-generering ---")
        print(f"SCHEMA: \n{db_schema_description}")
        print(f"FRÅGA: \n{natural_language_question}")
        print("-----------------------------------------------------------------\n")

        response = gemini_model_text_to_sql.generate_content(prompt)

        generated_sql = response.text.strip()

        if generated_sql.lower().startswith("```sql"): generated_sql = generated_sql[6:]
        elif generated_sql.lower().startswith("```"): generated_sql = generated_sql[3:]
        if generated_sql.lower().endswith("```"): generated_sql = generated_sql[:-3]
        generated_sql = generated_sql.strip().replace('`', '')

        print(f"DEBUG: Rått svar från Gemini (SQL): {response.text}")
        print(f"DEBUG: Rensad SQL från Gemini: {generated_sql}")
        
        if not generated_sql.upper().startswith("SELECT"):
            print(f"VARNING: Generarad SQL är inte en SELECT-sats: '{generated_sql}'")
            return "SELECT 'Ogiltig SWL genererad (inte en SELECT). ';"
        
        return generated_sql
    except Exception as e:
        error_msg = f"Fel vid generering av SQL från Gemini: {e}"
        print(error_msg)
        if hasattr(st, 'error'): st.error(error_msg)
        return "SELECT 'Tekniskt fel vid SQL-generering.';"
    
# --- RAG Q&A Funktion ---
def answer_question_with_rag(question: str, context_chunks: list[str]) -> str | None:
        global gemini_model_rag, gemini_api_key_configured

        if not gemini_api_key_configured or gemini_model_rag is None:
            error_msg = "FEL: Gemini RAG modell inte initierad. Kör configure_gemini() först. eller kontrollera API-nyckeln."
            print(error_msg)
            if hasattr(st, 'error'): st.error(error_msg)
            return "LLM-modell för RAG är inte tillgänglig."
        if not context_chunks:
            return "Jag kunde inte hitta tillräckligt med relevant information i jobbannonserna för att svara på din fråga."
        
        context_string = "\n---\n".join(context_chunks)
        
        prompt = f"""Du är en AI-assistent som hjälper till att svara på frågor baserat på information från jobbannonser.
        Svara på användarens fråga ENDAST baserat på följande kontext. Använd ingen extern kunskap.
        Om svaret inte tydligt framgår av kontexten, säg att infromationen inte finns i den tillhandahållna texten.
        Var koncis och direkt i ditt svar.

        Kontext fårn jobbannonser:
        ---
        {context_string}
        ---
        Användarens fråga: {question}
        Svar:"""

        try:
            print(f"\n--- Skickar följande prompt till Gemini för RAG-svar ---")
            print(f"FRÅGA: {question}")
            print(f"KONTEXT (början): \n{context_string[:500]}")
            print("--------------------------------------------------------\n")

            response = gemini_model_rag.generate_content(prompt)
            answer = response.text.strip()

            print(f"DEBUG: Rått svar från Gemini (RAG): {answer}")
            return answer
        except Exception as e:
            error_msg = f"Fel vid generering av RAG-svar från Gemini: {e}"
            print(error_msg)
            if hasattr(st, 'error'): st.error(error_msg)
            return "Ett tekniskt fel uppstod när jag försökte generera ett svar."
        

def get_qualities_from_gemini(job_descriptions_text, occupation_field):
    """ 
    Analyserar jobbannonsbeskrivningar med Gemini för att identifiera nyckelkvalifikationer.
    
    Args:
        job_descriptions_text (str): Text med jobbannonsbeskrivningar.
        occupation_field (str): Yrkesområden som analysen gäller för.

    Returns:
        str: En kommaseparerad sträng med de identifierade kvalifikationerna, eller None om API-nycklen saknas eller fel uppstår.
        """
    
    global gemini_api_key_configured
    
    if not gemini_api_key_configured:
        print("FEL: Försök anropa get_qualities_from_gemini utan konfiguerad API-nyckel.")
        st.error("API-nyckel för Gemini är inte konfiguerad. Vänligen säkerställ att GEMINI_API_KEY finns i Streamlit secrets eller som miljövariabel. ")
        return None
    
    if not genai.api_key:
        print("FEL: genai.api_key är inte satt trots att konfigurationen borde ha skett.")
        st.error("Ett internt fel med API-nyckelkonfigurationen.")
        return None
    
    try:
        model = genai.GenerativeModel("gemini-pro")

        prompt = f"""
        Analysera följande jobbannonsbeskrivningar för yrkesområdet '{occupation_field}':
        ---JOBBANNONSBESKRIVNINGAR---
        {job_descriptions_text}
        ---SLUT PÅ BESKRIVNINGAR---
        Baserat på texten ovan, identifiera och lista de 5-7 viktigaste och mest önskvärda kvalifikationerna, 
        färdigheterna eller egenskaperna som arbetsgivare söker hos den som söker jobb.
        Presentera dem som en tydlig, kommaseparerad lista. Undvik onödiga inledningsfraser.
        Exempel på output: "Kommunikativ, Problemlösare, Lagspelare, Erfarenhet av Python, Projektledning"
        """
        print(f"INFO: Skickar prompt till Gemini för yrkesområde: {occupation_field}")
        response = model.generate_content(prompt)


        if response and response.parts:
            extracted_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
            if extracted_text:
                print(f"INFO: Mottaget svar från Gemini: {extracted_text.strip()}")
                return extracted_text.strip()
            else:
                print("VARNING: Tom text extraherad från Gemini-svarets delar.")
                st.warning("Modellen retunerade ett svar men det var tomt. Försök igen eller justera input.")
                return None
    except Exception as e:
        print(f"FEL: Ett fel inträffade vid anrop till Gemini: {e}")
        if "API key not valid" in str(e):
            st.error("API-nyckel för Gemini är inte giltig. Kontrollera att den är korrekt inlagd.")
        elif "quota" in str(e).lower():
            st.error("API-kvoten för Gemini har troligen överskridits. Vänta och försök igen senare.")
        else:
            st.error("Ett internt fel uppstod vid anrop till Gemini.")
        return None