with dim_employer as (SELECT * FROM {{ ref('src_employer') }})

select 
{{dbt_utils.generate_surrogate_key(['employer_workplace', 'workplace_address__municipality'])}} as employer_id,
employer_name,
employer_workplace, 
employer_organization_number,
workplace_street_address, 
workplace_region, 
workplace_postcode, 
coalesce( {{capitalize("workplace_address__municipality") }}, 'ej_angiven') as workplace_municipality,
coalesce( {{capitalize("workplace_city") }}, 'ej_angiven') as workplace_city, 
workplace_country, 
from dim_employer