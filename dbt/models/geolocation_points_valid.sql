with typed as (
  select trim(geolocation_zip_code_prefix) zip_code, nullif(trim(geolocation_lat),'')::numeric latitude, nullif(trim(geolocation_lng),'')::numeric longitude, lower(trim(geolocation_city)) city, upper(trim(geolocation_state)) state, run_id source_run_id, source_row_number
  from {{ source('bronze','geolocation') }} where run_id='{{ var("source_run_id") }}'::uuid and nullif(trim(geolocation_lat),'')::numeric between -33.75 and 5.27 and nullif(trim(geolocation_lng),'')::numeric between -73.99 and -34.79
)
select distinct on (zip_code, latitude, longitude) *
from typed
order by zip_code, latitude, longitude, source_row_number
