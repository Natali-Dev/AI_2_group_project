with fct_job_ads as (select * from {{ ref('src_job_ads') }})


select
    {{ dbt_utils.generate_surrogate_key(['occupation__label']) }} as occupation_id,
    {{ dbt_utils.generate_surrogate_key(['id']) }} as job_details_id,
    {{ dbt_utils.generate_surrogate_key(['employer__workplace', 'workplace_address__municipality']) }} as employer_id,
    {{dbt_utils.generate_surrogate_key(['experience_required', 'driver_licence', 'access_to_own_car'])}} as attributes_id,
    {{dbt_utils.generate_surrogate_key(['language', 'l.job_id'])}} as language_id, --Behövs denna??
    vacancies,
    relevance,
    application_deadline,
    l.language, 
from fct_job_ads j
left join {{ ref('dim_languages') }} l on j.job_id = l.job_id