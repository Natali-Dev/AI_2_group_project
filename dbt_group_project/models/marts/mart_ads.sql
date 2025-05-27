with mart_ads AS ( 
    select  jb.headline, o.occupation, o.occupation_group, o.occupation_field, jb.description, 
    jb.duration, jb.working_hours_type, jb.scope_of_work_min, jb.scope_of_work_max, f.vacancies, e.employer_name, 
    e.workplace_region, e.workplace_city, aa.experience_required, aa.driving_license, aa.access_to_own_car, jb.must_have_languages
    from {{ ref('fct_job_ads') }} f
    left join {{ ref('dim_occupation') }} o on f.occupation_id = o.occupation_id
    left join {{ ref('dim_job_details') }} jb on f.job_details_id = jb.job_details_id
    left join {{ ref('dim_employer') }} e on e.employer_id = f.employer_id
    left join {{ ref('dim_auxilliary_attributes') }} aa on aa.auxilliary_attributes_id = f.auxilliary_attributes_id
)

from mart_ads