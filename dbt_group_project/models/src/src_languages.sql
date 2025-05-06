with src_language AS (
    select * from {{ source('job_ads', 'stg_language') }}
)

select label as language, _dlt_parent_id as job_id from src_language

