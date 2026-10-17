select zip_code, percentile_cont(0.5) within group (order by latitude) latitude, percentile_cont(0.5) within group (order by longitude) longitude, count(*) point_count, source_run_id
from (select distinct zip_code, latitude, longitude, source_run_id from {{ ref('geolocation_points_valid') }}) p group by zip_code, source_run_id
