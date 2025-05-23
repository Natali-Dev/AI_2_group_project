-- testar att scope_of_work_min <= scope_of_work_max
SELECT *
FROm {{ ref('dim_job_details') }}
WHERE scope_of_work_min > scope_of_work_max