


with installation_drift_underhall AS 
(
    Select * from {{ ref('mart_ads') }}
    where occupation_field = 'Installation, drift, underhåll' 
)

select * from installation_drift_underhall