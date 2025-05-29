# Dokumentation av dbt Tester för HR Analyticts Projektet

Detta dokument beskriver de dbt-tester som vi har använt i vårat projekt för att säkerställa datakvalitet och tillförlitlighet i vår HR-analyspipeline.

## Översikt av Implementerade Tester

Vi använder en kombination av standard-dbt-tester och anpassade tester för att säkerställa datakvalitet i vår HR-analyspipeline.
Baserat på resultaten från 'dbt test' inkluderar detta följande:

### 1. Standardtester (Generic Tests)

Dessa är inbyggda eller vanligt förekommande tester i dbt som konfigureras via 'schema.yml'-filer.

* **'not_null'**:
    * **Vad den kollar:** Att specifika kolumner **inte innehåller några tomma (NULL) värden.**
    * **Varför det är viktigt:** Kritiska datafält som ID:n, namn, eller nyckeltal ( t.ex. antal vakanser) måste finnas för att analysen ska vara meningsfull och för att undvika fel i dashboards. Om exempelvis 'employer_id' eller 'vacancies' saknas, blir datan opålitlig.
    * **Exempel i projektet:** 'not_null_dim_employer_employer_id', 'not_null_fct_job_ads_vacancies', ' not_null_mart_ads_headline'.

* **'unique'**:
    * **Vad den kollar:** Att alla värden i en specifierad kolumn är **unika.**
    * **Varför det är viktigt:** Används främst för primärnycklar i våra dimensionstabeller (t.ex. 'dim_employer.employer_id', dim_job_details.job_details_id'). Detta garanterar att varje entitet  (som en arbetsgivare eller en jobbdetalj) bara finns en gång, vilket är fundamentalt för korrekta relationer och aggregeringar.
    * **Exempel i projektet:** 'unique_dim_employer_employer_id', 'unique_dim_job_details_job_details_id'.

* **'accepted_values'**:
    * **Vad den kollar:** Att en kolumn **endast innehåller värden från en fördefinierad lista.**
    * **Varför det är viktigt:** Säkerställer att kategoriska data, som 'occupation_field' i våra 'mart'-tabeller är konsekventa och korrekta. Detta är särskilt viktigt då projektet specifierar att data som ska laddas för speficika yrkesområden. Testet förhindrar att felaktiga eller oväntade kategorier påverkar analysen för t.ex. "Kultur, media, design".
    
* **'relationships'** (Defineras i 'schema.yml, testar referensintegritet):
    * **Vad den kollar:** Att värden i en kolumn (en främmande nyckel) finns i en motsvarande kolumn i en annan tabell (oftast en primärnyckel).
    * **Varför är det viktigt:** Upprätthåller referensintegriteten mellan våra tabeller. Till exempel, varje 'occupation_id' i faktatabellen 'fct_job_ads' måste finnas i dimesionstabellen 'dim_occupation'. Detta förhindrar "föräldralösa" rader och säkerställer att våra datamodeller är korrekt länkade enligt den dimensionella modellen.

### 2. Anpassade Tester (Singular Tests / Custom Generic Tests)
Dessa är antingen SQL-filer i 'tests'-mappen eller anpassade generiska tester för att validera specifik affärslogik eller mer komplexa datakrav.

* **'dim_row_count_match_...'** (Anpassat makro):
    * **Vad den kollar:** Detta anpassade test (implementerat som ett makro i macros/tests/dim_row_count_match.sl') verifierar att antalet rader skapade i dimensionstabellen stämmer överens med relevnata källor.
    * **Varför det är viktigt:** Hjälper till att upptäcka  om data oväntat har förlorats eller duplicerats under transformationen till våra dimensionstabeller (som 'dim_employer' och 'dim_job_details', etc.).

* **'validate_application_deadline_format'** (Singular test i 'tests/validate_application_deadline_format.sql):
    * **Vad den kollar:** Säkerställer att kolumnen 'application_deadline följer ett specifikt datumformat.
    * **Varför det är viktigt:** Korrekt datumformatering är nödfvändig för tidsbaserade analyser, filtrering och för att undvika konverteringsfel i dashboards.

* **'validate_scope_of_work'** (Singular test i 'tests/validate_scope_of_work.sql'):
    * **Vad den kollar:** Validerar affärslogik relaterad till 'scope_of_work_min' och 'scope_of_work_max' i 'dim_job_details'. **T.ex. att minimivärdet inte överstiger maximivärdet.**
    * **Varför det är viktigt:** Garanterar logisk konsistens till datan som beskriver jobbomfattning.

* **'validate_vacancies'** (Singular test i 'tests/validate_vacancies.sql'):
    * **Vad den kollar:** Kontrollerar att värden i kolumnen 'vacancies' (t.ex i fvt_job_ads) är rimliga.
    * **Varför det är viktigt:**  Antal vakanser är ett centralt KPI för rekryteringsspecialisterna. Mycket viktigt!


## Hur Testerna Säkerställer Datakvalitet och Validerar Modeller

Den kombinerande effekten av dessa tester är att:
* **Validera datakvaliteten:** Vi identifierar och kan åtgärda problem som saknade värden, felaktiga format, oväntade kategorier och logiska inkonsekvenser.
* **Säkerställa modellernas integritet:** Testerna bekräftar at våra databasmodeller (staging, dimensioner, fakta, marts) är korrekt konstruerade coh att realtionerna mellan dem är giltiga.
* **Bygga förtroende för datan:**  Genom att kontinuerligt köra dessa tester kan man lita på den data och de insikter som presenteras i dashboarden för att fatta bättre beslut, samt effektivisera ens arbete.


För en fullständig och interaktiv översikt av alla modeller, kolumner tester och deras inbördes beroenden (data lineage), använder vi dbt's inbyggda dokumentationsfunktion.


**Så här genererar och visar du dbt-dokumentationen:**
1. Kör följande kommando i din terminal i dbt-projektets rotmap för att generera dokumentationsfilerna:
    '''bash
    dbt docs generate
    '''

2. Starta sedan en loka webbserver för att visa dokumentationen:
    '''bash
    dbt docs serve
    '''
Detta öppnar en webbsida i din webbläsare där du kan navigera genom projektets alla delar, se hur datan flödar, och förstå hur allt hänger ihop.

Genom att tillämpa dessa tester och tillhandahålla tydlig dokumentation strävar vi efter att leverera en robust och pålitligt datalösning.


