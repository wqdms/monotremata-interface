from django.utils.translation import gettext_lazy as _
from django.db import models
{% if project.category == 'gis' %}
from django.contrib.gis.db import models as gis_models
{% endif %}
from {{app_label}}.presets import AbstractMetaModelMixin, AbstractMetaModel, AbstractLifeCycleMetaModel
from {{app_label}}.presets import PresetModelField as Preset
from {{app_label}}.presets import PresetModelField

