with stg_attributes as (SELECT * FROM {{ source('job_ads', 'stg_ads') }})

select 
experience_required,
driving_license_required as driver_licence,
access_to_own_car
from stg_attributes