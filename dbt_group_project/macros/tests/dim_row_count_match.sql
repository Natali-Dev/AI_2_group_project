{% test dim_row_count_match(model, column_name) %}

    with fct as (
        select count(distinct {{ column_name }}) as fct_count
        from {{ ref('fct_job_ads') }}
    ),

    dim as (
        select count(*) as dim_count from {{ model }}
    )

    select * from fct, dim
    where fct.fct_count != dim.dim_count

{% endtest %}