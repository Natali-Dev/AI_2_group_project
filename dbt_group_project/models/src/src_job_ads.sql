with stg_job_ads as (
    select 
        id,
        headline,
        description__text as description,
        duration__label as duration,
        salary_type__label as salary_type,
        working_hours_type__label as working_hours_type,
        scope_of_work__min as scope_of_work_min,
        scope_of_work__max as scope_of_work_max,
        number_of_vacancies as vacancies,
        relevance,
        application_deadline,
        occupation_field__label as occupation_field,
        occupation__label,
        employer__workplace as employer_workplace,
        workplace_address__municipality as workplace_city,
        experience_required,
        driving_license_required,
        access_to_own_car
    from {{ source('job_ads', 'stg_ads') }}
)

select *
from stg_job_ads