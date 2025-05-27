{{
    config(
        materialized='view',
        schema='mart'
    )
}}

with mart_ads AS ( 
    select  
        jb.headline, 
        o.occupation,
        o.occupation_field,
        jb.scope_of_work_min,
        jb.scope_of_work_max,
        f.vacancies,
        e.workplace_city,
        aa.experience_required
    from {{ ref('fct_job_ads') }} f
    left join {{ ref('dim_occupation') }} o on f.occupation_id = o.occupation_id
    left join {{ ref('dim_job_details') }} jb on f.job_details_id = jb.job_details_id
    left join {{ ref('dim_employer') }} e on e.employer_id = f.employer_id
    left join {{ ref('dim_auxilliary_attributes') }} aa on aa.auxilliary_attributes_id = f.auxilliary_attributes_id
)

select * from mart_ads