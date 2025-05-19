with job_ads as (
    select * from {{ ref('src_employer') }}
)

select
    {{dbt_utils.generate_surrogate_key(['employer_workplace', 'workplace_address__municipality'])}} as employer_id,
    coalesce(employer_workplace, 'ej angiven') as employer_workplace,  
    coalesce(max(employer_name), 'ej angiven') as employer_name, 
    coalesce(max(employer_organization_number), 'ej angiven') as employer_organization_number, 
    coalesce(max(workplace_street_address), 'ej angiven') as workplace_street_address,  
    coalesce(max(workplace_postcode), 'ej angiven') as workplace_postcode, 
    coalesce(max({{capitalize('workplace_region')}}), 'ej angiven') AS workplace_region, 
    coalesce({{capitalize('workplace_address__municipality')}}, 'ej angiven') AS workplace_city, 
    coalesce(max(workplace_country), 'ej angiven') as workplace_country
from job_ads
group by employer_workplace, workplace_address__municipality


