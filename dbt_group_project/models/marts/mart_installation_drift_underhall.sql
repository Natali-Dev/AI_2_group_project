{{
    config(
        materialized='view',
        schema='mart'
    )
}}

select 
    workplace_city,
    COUNT(*) as antal_platser,
    AVG(vacancies) as genomsnittlig_platser_per_annons
from {{ ref('mart_ads') }}
where occupation_field = 'Installation, drift, underhåll'
group by workplace_city