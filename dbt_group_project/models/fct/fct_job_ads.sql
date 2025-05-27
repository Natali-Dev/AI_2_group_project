with job_ads as (select * from {{ ref('src_job_ads') }})

select
    {{ dbt_utils.generate_surrogate_key(['occupation__label']) }} as occupation_id,
    {{ dbt_utils.generate_surrogate_key(['id']) }} as job_details_id,
    {{ dbt_utils.generate_surrogate_key(['employer__workplace', 'workplace_address__municipality']) }} as employer_id,
    {{ dbt_utils.generate_surrogate_key(['experience_required','driving_license_required', 'access_to_own_car']) }} as auxilliary_attributes_id, 
    relevance,
    application_deadline,
    number_of_vacancies
from job_ads