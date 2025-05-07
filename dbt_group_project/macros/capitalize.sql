{% macro capitalize(column) %}
    upper(substr({{column}}, 1, 1)) || lower(substr({{column}}, 2))
{% endmacro %}