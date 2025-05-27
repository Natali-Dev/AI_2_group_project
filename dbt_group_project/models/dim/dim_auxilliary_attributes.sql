with job_ads as (
    select * from {{ ref('src_job_ads') }}
)

select 
    {{dbt_utils.generate_surrogate_key(['experience_required','driving_license_required', 'access_to_own_car'])}} as auxilliary_attributes_id,
    max(experience_required) as experience_required,
    max(driving_license_required) as driving_license,
    max(access_to_own_car) as access_to_own_car
from job_ads
group by auxilliary_attributes_id