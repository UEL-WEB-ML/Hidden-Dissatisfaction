{% test unique_combination_of_columns(model, combination_of_columns) %}

    select
        {% for column_name in combination_of_columns %}
        {{ adapter.quote(column_name) }}{% if not loop.last %}, {% endif %}
        {% endfor %},
        count(*) as combination_count
    from {{ model }}
    group by
        {% for column_name in combination_of_columns %}
        {{ adapter.quote(column_name) }}{% if not loop.last %}, {% endif %}
        {% endfor %}
    having count(*) > 1

{% endtest %}

{% test relationships_on_columns(model, to, columns) %}
select child.*
from {{ model }} as child
left join {{ to }} as parent
  on {% for column_name in columns %}child.{{ adapter.quote(column_name) }} = parent.{{ adapter.quote(column_name) }}{% if not loop.last %} and {% endif %}{% endfor %}
where {% for column_name in columns %}parent.{{ adapter.quote(column_name) }} is null{% if not loop.last %} or {% endif %}{% endfor %}
{% endtest %}
