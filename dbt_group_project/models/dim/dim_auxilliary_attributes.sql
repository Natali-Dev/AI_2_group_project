with job_ads as (
    select * from {{ source('job_ads', 'stg_ads') }}
)

select 
    {{dbt_utils.generate_surrogate_key(['id'])}} as auxilliary_attributes_id,
    experience_required,
    driving_license_required as driving_license,
    access_to_own_car
from job_ads
where id is not null