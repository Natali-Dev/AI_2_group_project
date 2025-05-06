with dim_languages AS
(
    select * from {{ ref('src_languages') }}
)

select language, job_id from dim_languages