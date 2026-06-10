{% load monotremata %}
{% if category == "gis" %}
class {{ className }}(gis_models.Model):
{% elif category == "simple" %}
class {{className}}(models.Model):
{% else %}
class {{className}}({{classParent}}):{% endif %}
    class Meta:
        abstract = {{ is_abstract }}
        ordering = {{ ordering_list }}
        app_label = "{{app_label}}"
        {% if verbose_name %}
        verbose_name = "{{ verbose_name }}"
        {% endif %}
        {% if verbose_name_plural %}
        verbose_name_plural = "{{ verbose_name_plural }}"
        {% endif %}
    {% for field in fields %}
    {{ field.fieldName }} = {{ field.fieldDataType }}({{ field.fieldParameters }})
    {% endfor %}{% if has_owner %}
    has_owner = Preset.has_owner('{{ app_label }}_{{className | lower }}_owner')
    {% endif %}
    {% if has_members %}
    has_members = Preset.has_members('{{ app_label }}_{{className | lower }}_members')
    {% endif %}
    is_private = Preset.booleanfield(default=False)
