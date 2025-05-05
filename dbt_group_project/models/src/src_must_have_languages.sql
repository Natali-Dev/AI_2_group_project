with source as (
    select * from {{ source('job_ads', 'stg_must_have_languages')}}
)

select
    _dlt_parent_id,
    label as language_label
from source
where label is not null