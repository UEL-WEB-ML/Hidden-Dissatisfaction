{% macro source_run_id() %}{{ var('source_run_id', '') | string }}{% endmacro %}

{% macro validated_source_run_id() %}
    {% set run_id = source_run_id() %}
    {# Parsing must be able to render model SQL without execution-time vars. #}
    {% if not execute %}
        {{ return('00000000-0000-4000-8000-000000000000') }}
    {% endif %}
    {% if not run_id or not modules.re.match('^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$', run_id) %}
        {{ exceptions.raise_compiler_error("--vars source_run_id=<uuid> is required") }}
    {% endif %}
    {{ return(run_id) }}
{% endmacro %}

{% macro validate_source_run_id() %}
    {% if not execute %}
        {{ return('') }}
    {% endif %}
    {% set run_id = validated_source_run_id() %}
    {% set result = run_query("select count(*) from " ~ source('bronze', 'ingestion_runs') ~ " where run_id = '" ~ run_id ~ "'::uuid and lower(status) = 'complete'") %}
    {% if result is none or result.columns[0].values()[0] | int != 1 %}
        {{ exceptions.raise_compiler_error("source_run_id must identify exactly one COMPLETE bronze.ingestion_runs row") }}
    {% endif %}
{% endmacro %}

{% macro bronze_source(relation_name, alias) %}
(select * from {{ source('bronze', relation_name) }}
 where run_id = '{{ validated_source_run_id() }}'::uuid) {{ alias }}
{% endmacro %}
