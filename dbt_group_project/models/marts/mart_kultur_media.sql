{# with job_ads as (
    select * from {{ ref('fct_job_ads') }}
),
occupation as (
    select * from {{ ref('dim_occupation') }}
)

select 
    job_ads.*,
    occupation.occupation_field
from job_ads
join occupation 
    on job_ads.occupation_id = occupation.occupation_id
where occupation.occupation_field = 'Kultur, media, design' #}

with kultur AS 
( 
    select * from {{ ref('mart_ads') }}
    where occupation_field = 'Kultur, media, design'
)

select * from kultur