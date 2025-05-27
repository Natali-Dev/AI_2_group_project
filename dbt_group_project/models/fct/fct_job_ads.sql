with job_ads as (select * from {{ ref('src_job_ads') }})

select
    {{ dbt_utils.generate_surrogate_key(['occupationlabel']) }} as occupation_id,
    {{ dbt_utils.generate_surrogate_key(['id']) }} as job_details_id,
    {{ dbt_utils.generate_surrogate_key(['employerworkplace', 'workplace_address__municipality']) }} as employer_id,
    {{ dbt_utils.generate_surrogate_key(['experience_required','driving_license_required', 'access_to_own_car']) }} as auxilliary_attributes_id,
        coalesce((number_of_vacancies), 1) as vacancies, 
    relevance,
    application_deadline
from job_ads