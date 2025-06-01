-- File: dbt_group_project/models/marts/mart_ads.sql

WITH fct_job_ads_data AS (
    SELECT * FROM {{ ref('fct_job_ads') }}
),

dim_occupation_data AS (
    SELECT * FROM {{ ref('dim_occupation') }}
),

dim_job_details_data AS (
    SELECT * FROM {{ ref('dim_job_details') }}
),

dim_employer_data AS (
    SELECT * FROM {{ ref('dim_employer') }}
),

dim_aux_attributes_data AS (
    SELECT * FROM {{ ref('dim_auxilliary_attributes') }}
),

-- Denna CTE bygger den denormaliserade mart-tabellen
mart_ads_cte AS (
    SELECT
        -- Nycklar och kolumner från fct_job_ads (aliaserad som 'f')
        f.job_details_id,         
        f.occupation_id AS fct_occupation_id, 
        f.employer_id AS fct_employer_id,     
        f.auxilliary_attributes_id AS fct_auxilliary_attributes_id, 
        f.publication_date AS ad_publication_date, 
        f.application_deadline AS ad_application_deadline,
        f.vacancies,
        f.relevance,

        -- Kolumner från dim_job_details (jb)
        jb.headline,
        jb.description,         
        jb.description_html,    
        jb.duration,            
        jb.working_hours_type,  
        jb.scope_of_work_min,
        jb.scope_of_work_max,
        jb.salary_type,
        jb.salary_description,
        jb.must_have_languages, 
        -- Om du lägger till t.ex. 'must_have_skills' i dim_job_details.sql, lägg till jb.must_have_skills här

        -- Kolumner från dim_occupation (o)
        o.occupation AS occupation_name, 
        o.occupation_group,              
        o.occupation_field,              
        o.occupation_id AS occupation_field_id, 

        -- Kolumner från dim_employer (e)
        e.employer_name,
        e.employer_organization_number,
        e.employer_workplace,
        e.workplace_street_address,
        e.workplace_postcode,
        e.workplace_city,
        e.workplace_region,
        e.workplace_country,
        -- Om du lägger till longitude/latitude i dim_employer.sql, lägg till dem här

        -- Kolumner från dim_auxilliary_attributes (aa)
        aa.experience_required,
        aa.access_to_own_car,
        aa.driving_license 

    FROM fct_job_ads_data f -- Alias 'f' används här
    LEFT JOIN dim_occupation_data o ON f.occupation_id = o.occupation_id
    LEFT JOIN dim_job_details_data jb ON f.job_details_id = jb.job_details_id
    LEFT JOIN dim_employer_data e ON f.employer_id = e.employer_id
    LEFT JOIN dim_aux_attributes_data aa ON f.auxilliary_attributes_id = aa.auxilliary_attributes_id
)

SELECT * FROM mart_ads_cte
