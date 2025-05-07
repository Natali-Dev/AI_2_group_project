with job_ads as (
    select * from {{ ref('src_employer') }}
)

select
    {{dbt_utils.generate_surrogate_key(['employer_workplace', 'workplace_address__municipality'])}} as employer_id,
    employer_workplace, 
    employer_name,
    employer_workplace, 
    employer_organization_number,
    workplace_street_address, 
    workplace_postcode,
    coalesce ({{capitalize('workplace_region')}}, 'ej angiven') AS workplace_region, 
    coalesce({{capitalize('workplace_address__municipality')}}, 'ej angiven') AS workplace_city, 
    workplace_country, 
from job_ads


