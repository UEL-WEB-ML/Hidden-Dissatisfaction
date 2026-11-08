select g.run_id as source_run_id, geolocation_zip_code_prefix::text, geolocation_lat::double precision, geolocation_lng::double precision, lower(nullif(trim(geolocation_city::text), '')) as geolocation_city, upper(nullif(trim(geolocation_state::text), '')) as geolocation_state
from {{ bronze_source('olist_geolocation', 'g') }}
