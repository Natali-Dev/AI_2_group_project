with kultur AS 
( 
    select * from {{ ref('mart_ads') }}
    where occupation_field = 'Kultur, media, design'
)

select * from kultur