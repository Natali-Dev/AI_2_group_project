with job_ads as (
    select * from {{ source('job_ads', 'stg_ads') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['id']) }} as employer_id,
    employer__name as employer_name,
    employer__workplace as employer_workplace,
    employer__organization_number as employer_organization_number,
    workplace_address__street_address as workplace_street_address,
    workplace_address__region as workplace_region,
    workplace_address__postcode as workplace_postcode,
    workplace_address__municipality as workplace_city,
    workplace_address__country as workplace_country
from job_ads
where id is not null

