with stg_job_ads as (select * from {{ source('job_ads', 'stg_ads') }})


select
    _dlt_id as job_id,
    occupation__label,
    id,
    employer__workplace,
    workplace_address__municipality,
    number_of_vacancies as vacancies,
    relevance,
    application_deadline,
    experience_required, 
    driving_license_required as driver_licence, 
    access_to_own_car,
from stg_job_ads