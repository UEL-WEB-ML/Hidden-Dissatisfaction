select source_run_id, geolocation_zip_code_prefix::text as zip_code_prefix, percentile_cont(0.5) within group (order by geolocation_lat) as lat, percentile_cont(0.5) within group (order by geolocation_lng) as lng, count(*)::int as n_points
from {{ ref('stg_geolocation') }}
where geolocation_lat between -33.8 and 5.3 and geolocation_lng between -74.0 and -34.7
group by source_run_id, geolocation_zip_code_prefix
