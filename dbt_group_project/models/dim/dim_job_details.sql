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
    jdb.headline,
    jdb.description,
    jdb.description_html,
    coalesce(jdb.duration, 'ej angiven') as duration,
    jdb.salary_type,
    jdb.salary_description,
    jdb.working_hours_type,
    jdb.scope_of_work_min,
    jdb.scope_of_work_max,
    coalesce(la.must_have_languages_list, 'ej angiven') as must_have_languages

from job_details_base jdb
left join languages_agg la
    on jdb._dlt_id = la._dlt_parent_id