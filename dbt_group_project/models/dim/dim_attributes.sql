with dim_attributes AS 
(
    SELECT * FROM {{ ref('src_attributes') }}
)

select 
{{dbt_utils.generate_surrogate_key(['experience_required', 'driver_licence', 'access_to_own_car'])}} as attributes_id,
max(experience_required) as experience_required,
max(driver_licence) as driver_licence,
max(access_to_own_car) as access_to_own_car
from dim_attributes
group by attributes_id