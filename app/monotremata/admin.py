from django.apps import apps
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
import logging
from django.http import HttpResponse, FileResponse
from django import forms

logger = logging.getLogger(__name__)
from monotremata import models
from monotremata.modelling import (
    OrganizationConfigLoader,
    ProjectZipFile,
    ProjectConfigLoader,
    ApplicationConfigLoader,
    DeploymentConfigLoader,
)



app_models = list(apps.get_app_config("monotremata").get_models())
exclude_list = [
    "description",
    "meta",
    "content",
    "template_from_raw_string",
    "template_from_file_path",
    "dependencies",
    "header",
    "footer",
    "template_string",
    "template_file",
    "template_url",
    "context",
    "fieldParameterss",
    "render_from",
    "sorting",
    "template_file",
    "template_string",
    "render_from",
    "template_url",
    "context",
]

admin.site.site_header = "Monotremata"
admin.site.site_title = admin.site.site_header

# admin.site.register(Site)


class EncryptedPasswordForm(forms.ModelForm):
    class Meta:
        model = models.Deployment
        fields = "__all__"
        widgets = {
            # render_value=False ensures even the hashed version is hidden
            "db_password": forms.PasswordInput(render_value=True),
            "git_organization_password": forms.PasswordInput(render_value=True),
        }


# @admin.action(description="set selected to application")
# def set_application_to_selected(modeladmin, request, queryset):
#     app = models.Application.objects.filter(
#         id=request.COOKIES.get("application")
#     ).first()
#     print([modeladmin, request, queryset])
#     for i in queryset:
#         i.application = app
#         i.save()


# # TODO
# @admin.action(description="deploy selected projects to cluster")
# def deploy_to_cluster(modeladmin, request, queryset):
#     for i in queryset:
#         pass


@admin.action(description="reload scripts, by setting lifecycle hook to reload")
def reload_scripts(modeladmin, request, queryset):
    for i in queryset:
        i.lifecycle_hook = "reload"
        i.save()


@admin.action(description="set selected as private")
def set_private(modeladmin, request, queryset):
    for i in queryset:
        i.is_private = True
        i.save()


@admin.action(description="unset selected as private")
def unset_private(modeladmin, request, queryset):
    for i in queryset:
        i.is_private = False
        i.save()


@admin.action(description="render template from string")
def render_srting(modeladmin, request, queryset):
    x = ""
    for i in queryset:
        i.render_from = "string"
        i.template_string = f"{type(i)}-{i}-" + "{{ name }}"
        x += i.get_admin_options(**{"app_label": "dono", "download": "string"})
    print(x)


@admin.action(description="do not render template from string")
def render_none(modeladmin, request, queryset):
    for i in queryset:
        i.render_from = None


def file_response(filename: str, zipped: ProjectConfigLoader):
    return FileResponse(
        zipped.get_zip_file(),
        as_attachment=True,
        filename=filename,
        content_type="application/octet-stream",
    )


@admin.action(description="download as zip folder")
def download_zip(modeladmin, request, queryset):
    result = []
    if modeladmin.model == models.Organization:
        for i in queryset:
            if not i.projects.all():
                pass
            else:
                ocl = OrganizationConfigLoader(i)
                result += ocl.load_zip()
        if result:
            zipped = ProjectZipFile(response=result)
            return file_response("organizations.zip", zipped)

    elif modeladmin.model == models.Project:
        for i in queryset:
            if not i.applications.all():
                pass
            else:
                ocl = ProjectConfigLoader(i)
                result += ocl.load_zip()
        if result:
            zipped = ProjectZipFile(response=result)
            return file_response("projects.zip", zipped)

    elif modeladmin.model == models.Application:
        for i in queryset:
            ocl = ApplicationConfigLoader(i)
            result += ocl.load_zip()
        zipped = ProjectZipFile(response=result)
        return file_response("appliacations.zip", zipped)

    elif modeladmin.model == models.Deployment:
        for i in queryset:
            if not i.applications.all():
                pass
            else:
                ocl = DeploymentConfigLoader(i)
                result += ocl.load_zip()
        if result:
            zipped = ProjectZipFile(response=result)
            return file_response("projects.zip", zipped)

    zipped = ProjectZipFile()
    return file_response("projects.zip", zipped)


@admin.action(description="add documents to preset model fields")
def process_documents(modeladmin, request, queryset):
    if modeladmin.model == models.Document:
        for i in queryset:
            i.lifecycle_hook = "process"
            i.save()

@admin.action(description="deploy to git")
def deploy_to_git(modeladmin, request, queryset):
    if modeladmin.model == models.Document:
        for i in queryset:
            i.lifecycle_hook = "deploy"
            i.save()

    # x=""
    # for i in queryset:

    #     x += i.get_admin_options(**{"app_label":"dono","download":"string"})
    # print(x)
    # response = FileResponse()
    # return response


# @admin.action(description="set selected as public")
# def set_public(modeladmin, request, queryset):
#     for i in queryset:
#         i.is_public = True
#         i.save()


# @admin.action(description="unset selected as public")
# def unset_public(modeladmin, request, queryset):
#     for i in queryset:
#         i.is_public = False
#         i.save()


def load_dynamic_admin(app_models):
    for model in app_models:
        # Create a dynamic Admin class
        class DynamicAdmin(ImportExportModelAdmin):
            if model in [models.Deployment]:
                form = EncryptedPasswordForm
            actions = []
            # actions = [set_private, unset_private]
            if model in [
                models.Organization,
                models.Project,
                models.Application,
                models.Deployment,
            ]:
                actions.append(download_zip)
            if model in [models.Document]:
                actions.append(process_documents)
            if model in [models.Deployment]:
                actions.append(reload_scripts)
                actions.append(deploy_to_git)


            if "is_private" in [i.name for i in model._meta.fields]:
                actions += [set_private, unset_private]

            list_filter = [
                field.name
                for field in model._meta.fields
                if field.name not in [*exclude_list, "name"]
            ] + ["tag", "render_from"]
            verbose_name = model.__name__
            list_display = [
                field.name
                for field in model._meta.fields
                if field.name not in exclude_list + ["script"]
            ]
            readonly_fields = ["id"]

            def get_readonly_fields(self, request, obj=None):
                if hasattr(obj, "has_owner") and not request.user.is_superuser:
                    return self.readonly_fields + ["has_owner"]
                if hasattr(obj, "file_upload"):
                    if obj.file_upload:
                        return self.readonly_fields + [
                            "file_upload",
                            "file_format",
                            "file_size",
                        ]
                return self.readonly_fields

            def get_list_filter(self, request):
                response = super().get_list_filter(request)
                if self.model in [
                    models.Organization,
                    models.Project,
                    models.Application,
                    models.PresetModel,
                    models.PresetModelField,
                ]:
                    response.append("domains__name")
                return response

            def save_model(self, request, obj, form, change):
                if hasattr(obj, "has_owner"):
                    if not obj.has_owner:
                        obj.has_owner = request.user
                # if hasattr(obj, "has_members") and hasattr(obj,"id"):
                #     obj.has_members.add(request.user)
                super().save_model(request, obj, form, change)

            def get_fields(self, request, obj=...):
                response = super().get_fields(request, obj)
                __list_filter = [
                    field for field in response if field not in [*exclude_list]
                ] + ["description","context"]

                return __list_filter

            def get_db_field_attr(self, request, obj, attr, **kwargs):
                if hasattr(obj, attr):
                    f = super().get_form(request, obj, **kwargs)
                    f.base_fields[attr].help_text = "Note: type to overwrite."
                    return f
                return None

            def get_form(self, request, obj=..., change=..., **kwargs):
                self.get_db_field_attr(request, obj, "db_password", **kwargs)
                self.get_db_field_attr(
                    request, obj, "git_organization_password", **kwargs
                )

                return super().get_form(request, obj, change, **kwargs)

        try:
            admin.site.register(model, DynamicAdmin)
        except admin.sites.AlreadyRegistered:
            pass
    return admin


load_dynamic_admin(app_models)
