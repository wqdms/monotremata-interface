from django.contrib import admin
        
from {{ app_label }}.presets import load_dynamic_admin
        
from django.apps import apps
        
app_models = list(apps.get_app_config('{{ app_label }}').get_models())
        
admin.site.site_header = '{{ project_folder }}'
        
admin.site.site_title = '{{ project_folder }}'
        
load_dynamic_admin(app_models)
        