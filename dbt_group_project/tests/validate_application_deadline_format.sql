-- Testar att application_deadline är ett giltigt datum
SELECT *
FROM {{ ref('fct_job_ads') }}
WHERE TRY_CAST(application_deadline AS DATE) IS NULL