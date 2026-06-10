from django import template
from django.template import Template, Context
from django.conf import settings
from datetime import datetime
from monotremata import models
import os
from django.template.loader import get_template

register = template.Library()


@register.simple_tag
def mono_render_context(flatpage):
    rendered = Template(flatpage.content).render(
        Context(
            {
                "projects": models.Project.objects.values(
                    "name", "id", "tag", "label", "description"
                ),
                "UPDATED_CONTENT": str(datetime.now()),
                "GIT_HOST": settings.GIT_HOST,
                "SERVICE_HOST": settings.SERVICE_HOST,
            }
        )
    )
    return rendered

@register.simple_tag
def mono_render_folder(wrapper_file_path:str,content_folder_path:str,css_class_names:str=None):
    files_folder = settings.BASE_DIR / "templates" / content_folder_path
    if os.path.exists(files_folder):
        templates = [f"{content_folder_path}/{x}" for x in [i for i in os.walk(files_folder)][0][2]]
        templates.sort()
        rendered = get_template(wrapper_file_path).render(context={
            "templates":templates
        })

    # rendered = Template(flatpage.content).render(
    #     Context(
    #         {
    #             "projects": models.Project.objects.values(
    #                 "name", "id", "tag", "label", "description"
    #             ),
    #             "UPDATED_CONTENT": str(datetime.now()),
    #             "GIT_HOST": settings.GIT_HOST,
    #             "SERVICE_HOST": settings.SERVICE_HOST,
    #         }
    #     )
    # )
    return rendered
