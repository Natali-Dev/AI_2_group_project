import streamlit as st
# from chart_kpi import vacancies_by_group, chart_top_occupations

# from kultur_dashboard import show_metric
import duckdb
import plotly.express as px
import os
from google import genai
import os
import pandas as pd
import json
from dotenv import load_dotenv
import duckdb
# from chart_kpi import current_df

# from kultur_dashboard import df_kultur

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# with duckdb.connect("../../../ads_data.duckdb") as con:
#     df_kultur = con.execute("SELECT * FROM mart.mart_kultur_media").df()
# få en kort förklaring om datan
# plotta datan
# st.write("Vilka krav och meriterande egenskaper är vanligast inom top 1 [sort_on]")
# st.write("Vilken stad har bäst möjligheter inom [Workplace City]")
# st.write("Skapa en lista på frågor en rekryterare bör ställa vid en intervju för [occuppation]")
# st.write("Vilka kompetenser efterfrågas mest i [Workplace City] just nu?")
# st.write("")
# st.write("")
# st.write("")
def gemini_layout(current_df):

    field = "Kultur, Media, Design"
    # sort_on = st.selectbox("Sortera på", ["Workplace City", "employer_name", "occupation"])
    # fig = chart_top_occupations(field, sort_on)
    # st.plotly_chart(fig)
    st.markdown("## Ställ en fråga till Gemini")  # baserat på grafen?
    # vilken utbildning krävs? #belasningsregister #i vilken stad finns minst krav och vilka är dessa #vilken stad har mest krav
    category = st.selectbox(
        "Välj en kategori:", ["workplace_city", "employer_name", "occupation"]
    )
    choice_sort = st.selectbox(
        "välj en stad/arbetsgivare/yrke", current_df[category].sort_values().unique()
    )
    choice_question = st.selectbox(
        "Välj en fråga",
        [
            "Select...",
            f"Vad är de vanligaste kraven och meriterna inom {choice_sort}?",
            f"Vad är de vanligaste arbetsuppgifterna inom {choice_sort}?",
            f"",
        ],
    )
    # Matcha person med jobb, skriva in nyckelord och sök efter matchande annonser i städer/ hos arbetsgivare / på yrken

    # choice_input = st.text_input(f"Ställ en egen fråga", {choice_sort})
    # st.write(text)
    # st.write() #sammanfattning av datan
    if choice_question != "Select...":
        text = gemini_logic(current_df,category, choice_sort, choice_question)
        st.write(text)
    # fig_krav, fig_meriterande = plot_gemini(text)
    # st.plotly_chart(fig_krav)
    # st.plotly_chart(fig_meriterande)
    # utgå ifrån vilken field som är vald


# if __name__ == "__main__":
#     pass


def gemini_logic(current_df,category, choice_sort, choice_question):
    top_employer = (
        current_df.groupby(category)[["vacancies", "description"]]
        .sum()
        .sort_values(by="vacancies", ascending=False)
        .reset_index()
    )
    nr_1 = top_employer[top_employer[category] == choice_sort]
    st.write(nr_1)
    # nr_1 = top_employer[["employer_name","description"]].iloc[2]
    nr_1.to_csv("for_gemini.txt")
    # with open("for_gemini.txt", "w") as file:
    #     file.write(nr_1)
    # nr_1["description"].

    with open("for_gemini.txt", "r", encoding="utf-8") as file:
        ad_text = file.read()

    # Plocka ut de 5 vanligaste kraven de 5 vanligaste meriterade och antal av dessa som efterfrågas i dessa jobbannonser, samt en sammanfattning av krav och meriter som du skriver ut:
    promt = f"""Du är en rekryterare inom Media, Kultur, Design.
    Svara på denna fråga: {choice_question} Genom att läsa dessa annonser, sammanfattat: 
    {ad_text}

    """
    # Output ska vara i detta formatet enbart:
    # {{
    #     "sammanfattning": ["sammanfattning"]

    # }}
    # "krav": [erfarenhet1, erfarenhet2, ...]
    # "antal krav": [summa erfarenhet1.., summa erfarenhet2]
    # "meriterande": [meriterande1,meriterande2, ... ]
    # "antal meriterande": [summa meriterande1.., summa meriterande2]
    response = client.models.generate_content(model="gemini-2.0-flash", contents=promt)
    print(response.text)
    text = response.text

    # cleaned = data.strip("```json") #.replace("\n", "").strip().replace("  ", "")
    # data = json.loads(cleaned)
    # text = pd.DataFrame({
    #     "sammanfattning": data["sammanfattning"]
    # })
    # df = pd.DataFrame({
    #     "krav": data["krav"],
    #     "antal krav": data["antal krav"],
    #     "meriterande": data["meriterande"],
    #     "antal meriterande": data["antal meriterande"]

    # })
    # return df
    return text


def plot_gemini(df):
    fig_krav = px.bar(df, y="antal krav", x="krav")
    fig_meriterande = px.bar(df, y="antal meriterande", x="meriterande")
    return fig_krav, fig_meriterande
