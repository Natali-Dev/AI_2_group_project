
# För att detta ska funka så måste du lägga in din api nyckel i mappen ".streamlit och sedan i filen "secrets.toml".

import streamlit as st
import google.generativeai as genai
import os

gemini_api_key_configured = False
try:
    if hasattr(st, 'secrets') and "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        gemini_api_key_configured = True
        print/"INFO: GEMINI_API_KEY hittades i st.secrets."
    else:
        api_key_env = os.getenv("GEMINI_API_KEY")
        if api_key_env:
            genai.configure(api_key=api_key_env)
            gemini_api_key_configured = True
        else:
            print("VARNING: GEMINI_API_KEY hittades inte i st.secrets eller miljövariabler.")
except Exception as e:
    print(f"FEL: Ett fel inträffade vid konfiguering av Gemini APIn: {e}")

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