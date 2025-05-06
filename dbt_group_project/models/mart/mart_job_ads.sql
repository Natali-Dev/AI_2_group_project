with mart_ads AS (

select  jb.headline, o.occupation, o.occupation_group, o.occupation_field, jb.description, 
jb.duration, jb.working_hours_type, jb.scope_of_work_min, jb.scope_of_work_max, f.vacancies, e.employer_name, 
e.workplace_region, e.workplace_municipality as municipality, a.experience_required, a.driver_licence, a.access_to_own_car, l.language

from {{ ref('fct_job_ads') }} f
left join {{ ref('dim_occupation') }} o on f.occupation_id = o.occupation_id
left join {{ ref('dim_job_details') }} jb on f.job_details_id = jb.job_details_id
left join {{ ref('dim_employer') }} e on e.employer_id = f.employer_id
left join {{ ref('dim_attributes') }} a on a.attributes_id = f.attributes_id
left join {{ ref('dim_languages') }} l on l.job_id = f.language_id
)

select * from mart_ads