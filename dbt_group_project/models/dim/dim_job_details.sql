with job_details_base as (
    select * from {{ ref('src_job_details') }}
),

job_languages as (
    select * from {{ ref('src_must_have_languages') }}
),

languages_agg as (
    select
        _dlt_parent_id,
        string_agg(language_label, ', ' ORDER BY language_label) as must_have_languages_list
        from job_languages
        group by _dlt_parent_id
)

select
    {{ dbt_utils.generate_surrogate_key(['jdb.id']) }} as job_details_id,
    coalesce(jdb.headline, 'ej angiven') as headline,
    coalesce(jdb.description, 'ej angiven') as description,
    coalesce(jdb.description_html, 'ej angiven') as description_html,
    coalesce(jdb.duration, 'ej angiven') as duration,
    coalesce(jdb.salary_type, 'ej angiven') as salary_type, 
    coalesce(jdb.salary_description, 'ej angiven') as salary_description, 
    coalesce(jdb.working_hours_type,'ej angiven') as working_hours_type,
    scope_of_work_min, --är int
    scope_of_work_max, -- är int
    coalesce(la.must_have_languages_list, 'ej angiven') as must_have_languages

from job_details_base jdb
left join languages_agg la
    on jdb._dlt_id = la._dlt_parent_id