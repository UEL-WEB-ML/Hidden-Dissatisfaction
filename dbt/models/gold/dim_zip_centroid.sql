select source_run_id, zip_code_prefix, lat, lng, n_points
from {{ ref('geolocation_zip') }}
