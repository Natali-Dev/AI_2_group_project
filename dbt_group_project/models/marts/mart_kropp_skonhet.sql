with kropp_skonhet AS 
(
    Select * from {{ ref('mart_ads') }}
    where occupation_field = 'Kropps- och skönhetsvård' 
)

select * from kropp_skonhet