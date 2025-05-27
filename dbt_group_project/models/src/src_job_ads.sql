with stg_job_ads as (
    select 
        id,
        headline,
        description__text,
        duration__label,
        salary_type__label,
        working_hours_type__label,
        scope_of_work__min,
        scope_of_work__max,
        number_of_vacancies,
        relevance,
        application_deadline,
        occupation_field__label,
        occupation__label,
        employer__workplace,
        workplace_address__municipality,
        experience_required,
        driving_license_required,
        access_to_own_car,
    from {{ source('job_ads', 'stg_ads') }}
)

select *
from stg_job_ads