import os
from pathlib import Path
from django.conf import settings
from typing import List, Optional, Any
import json
from django.apps import apps
from django.core.management import call_command
from django.core.management.base import CommandError
from django.template import Template, Context
from django.template.loader import get_template
import io
import zipfile
from datetime import datetime
import re


class ProjectZipFile:
    def __init__(
        self,
        save_path: Path = None,
        response: list[dict] = [
            {
                "folder": "",
                "file": "no-content.txt",
                "content": f"# missing content | {datetime.now()}",
            }
        ],
    ):
        self.zip_buffer = io.BytesIO()
        self.response = response if response else list()
        self.save_path = save_path

    def add_response(self, folder, file, content):
        """object response structure"""
        data = {"file": file, "folder": folder, "content": content}
        self.response.append(data)
        return data

    def zip_project(self):
        with zipfile.ZipFile(
            self.zip_buffer,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as zf:
            for i in self.response:
                zf.writestr(os.path.join(i["folder"], i["file"]), i["content"])

    def get_zip_file(self):
        self.zip_project()
        self.zip_buffer.seek(0)
        return self.zip_buffer

    def zip_as_folder(self):
        if self.save_path:
            with open(self.save_path, "wb") as project:
                project.write(self.get_zip_file().getvalue())
        else:
            raise ValueError("missing: save_path")

    def unzip_file(self):
        if self.save_path:
            with zipfile.ZipFile(self.save_path, "r") as zip:
                zip.extractall(self.save_path.replace(".zip", ""))


class FieldDefinition:
    """
    An entity–attribute–value model (EAV) is a data model optimized for the space-efficient storage of sparse—or ad-hoc—property or data values,
    intended for situations where runtime usage patterns are arbitrary, subject to user variation, or otherwise unforeseeable using a fixed design.
    """

    def __init__(self, fieldName, fieldDataType, fieldParameters):
        self.fieldDataType: str = fieldDataType
        self.fieldName: str = fieldName
        self.fieldParameters: str[Any] = fieldParameters

    def __call__(self):
        return self.__dict__

    def get(self, attr):
        return self.__dict__.get(attr)


class ModelBuild:
    """
    EAV is also known as object–attribute–value model, vertical database model, and open schema.
    """

    def __init__(
        self,
        className: str,
        classParent: str = "AbstractMetaModel",
        fields: Optional[List[FieldDefinition | dict]] = None,
        is_abstract: bool = False,
        ordering_list: list[str] = ["sorting"],
        app_label: str = "monotremata",
        verbose_name: str = None,
        verbose_name_plural: str = None,
        serializerClassParent: str = "serializers.ModelSerializer",
        viewsetClassParent: str = "viewsets.ModelViewSet",
        category: str = None,
        **kwargs,
    ):
        self.className = className
        self.classParent = classParent
        self.fields = fields
        self.is_abstract = is_abstract
        self.ordering_list = ordering_list
        self.app_label = app_label
        self.verbose_name = verbose_name
        self.verbose_name_plural = verbose_name_plural
        self.serializerClassParent = serializerClassParent
        self.viewsetClassParent = viewsetClassParent
        self.category = category

    def get_model_template(self, overwrite: dict = dict(), prepend: dict = dict()):
        # fields = "\n\tpass"
        # if self.fields:
        #     fields = ""
        #     for i in self.fields:
        #         fields += f"\n\t{i.get("fieldName")} = {i.get("fieldDataType")}({i.get("fieldParameters")})"
        
        template = get_template("models.py").render(
            context={**prepend, **self.__dict__, "fields": self.fields, **overwrite}
        )
        tmp = re.sub(r"\n\s*\n", "\n", template)
        return tmp

    def get_serializer_template(self):
        template = f"""
        \nclass {self.className}ModelSerializer({self.serializerClassParent}):
        \n\tclass Meta:
        \n\t\tmodel = models.{self.className}
        \n\t\tfields = "__all__"
        """
        return template

    def get_views_template(self):
        template = get_template("views.py").render(context=self.__dict__)

        return template

    def get_router_template(self):
        template = f"""
        \nrouter.register("{self.className.lower()}",views.{self.className}ModelViewSet,basename="{self.className.lower()}")
        """
        return template

    def __call__(self, *args, **kwds):
        "testing model build in memory"
        exec(self.get_template())
        return self.className


class ModelConfigLoader:
    def __init__(
        self,
        model_build_class: ModelBuild = ModelBuild,
        app_label: str = "",
        project_folder: str = "",
        organization_folder: str = "",
        model_definitions: list = list(),
        category: str = None,
        db_driver: str = None,
        **kwargs,
    ):
        self.model_definitions = model_definitions
        self.model_build_class: ModelBuild = model_build_class
        self.app_label: str = app_label.lower()
        self.project_folder = Path(str(project_folder).lower())
        self.organization_folder = organization_folder.lower()
        self.app_labels = [self.app_label]
        self.base_path = self.organization_folder
        self.proj_path = f"{self.base_path}/{self.project_folder}"
        self.interface_path = f"{self.proj_path}/interface"
        self.category = category
        self.db_driver = db_driver
        self.kwargs = kwargs

    def load_from_settings(self, *args, **kwargs):
        """load settings.MONOTREMATA_MODEL_DEFINITIONS json config files"""
        try:
            apps.get_app_config(self.app_label)
        except LookupError:
            try:
                call_command("startapp", self.app_label)
            except CommandError:
                pass
        # load definitions from json
        for i in settings.MONOTREMATA_MODEL_DEFINITIONS:
            if os.path.exists(i):
                with open(i, "r") as f:
                    self.model_definitions += json.load(f)

    def load_from_files(self, array: list[str], *args, **kwargs):
        for i in array:
            if os.path.exists(i):
                with open(i, "r") as f:
                    self.model_definitions += json.load(f)

    def app_model_loader(self, pmodel, app):
        return {
            **self.__dict__,
            **pmodel,
            **{
                "app_label": self.app_label,
                "fields": app.preset_models.filter(id=pmodel["id"])
                .first()
                .fields.values(),
            },
        }

    def load_from_organization(self, organization):
        model_definitions = []
        for p in organization.projects.all():
            for a in p.applications.all():
                for m in a.preset_models.all().values():
                    model_definitions.append(self.app_model_loader(m, a))

        self.model_definitions = model_definitions
        return self.model_definitions

    def load_from_application(self, app):
        model_definitions = []
        for m in app.preset_models.all().values():
            model_definitions.append(
                model_definitions.append(self.app_model_loader(m, app))
            )

        self.model_definitions = model_definitions
        return self.model_definitions

    def get_models_template(self, *args, **kwargs):
        """write models.py"""

        tmp = get_template("models_import.py").render(
            context={**self.__dict__, **kwargs}
        )

        for model in self.model_definitions:
            if model:
                tmp += self.model_build_class(
                    **{**model, **self.__dict__, "app_label": self.app_label}
                ).get_model_template()
        return tmp

    def get_serializers_template(self, *args, **kwargs):
        """write serializers.py"""
        tmp = f"""
        \nfrom rest_framework import serializers
        \nfrom {self.app_label} import models
        """
        for model in self.model_definitions:
            if model:
                if not model.get("is_abstract"):
                    tmp += self.model_build_class(
                        **{**model, "app_label": self.app_label}
                    ).get_serializer_template()
        return tmp

    def get_views_template(self, *args, **kwargs):
        """write views.py"""
        tmp = f"""
        \nfrom rest_framework import viewsets, permissions, renderers, filters
        \nfrom django_filters.rest_framework import DjangoFilterBackend
        \nfrom django.db.models import Q
        \nfrom {self.app_label} import models
        \nfrom {self.app_label} import serializers
        """
        for model in self.model_definitions:
            if model:
                if not model.get("is_abstract"):
                    tmp += self.model_build_class(
                        **{**model, "app_label": self.app_label}
                    ).get_views_template()
        return tmp

    def get_urls_template(self, *args, **kwargs):
        """write views.py"""
        tmp = f"""
        \nfrom rest_framework.routers import DefaultRouter
        \nfrom {self.app_label} import views
        \nrouter = DefaultRouter()
        """
        for model in self.model_definitions:
            if model:
                if not model.get("is_abstract"):
                    tmp += self.model_build_class(
                        **{**model, "app_label": self.app_label}
                    ).get_router_template()
        tmp += "\nurlpatterns=router.urls"
        return tmp

    def get_admin_template(self, *args, **kwargs):

        tmp = self.render_template(
            settings.BASE_DIR / "monotremata" / "templates" / "admin.py",
            context={**self.__dict__},
        )
        return tmp

    def get_apps_template(self, *args, **kwargs):
        template = f"""from django.apps import AppConfig
        \nclass {self.app_label.capitalize()}Config(AppConfig):
        \n\tname = "{self.app_label.lower()}"
        """
        return template

    def get_interface_urls_template(self, *args, **kwargs):
        tmp = self.render_template(
            settings.BASE_DIR / "monotremata" / "templates" / "urls.py",
            context={**self.__dict__},
        )
        return tmp

    def read_template(self, file_path: Path, *args, **kwargs):
        with open(file_path, "r") as f:
            return f.read()

    def render_template(self, file_path: Path, context: dict):
        t = Template(self.read_template(file_path))
        return t.render(context=Context(context))

    def write_template(self, preset_file_path, callback: str, *args, **kwargs):
        with open(preset_file_path, "w") as f:
            f.write(getattr(self, callback)(*args, **kwargs))

    def write_a_file(self, file_path, content):
        with open(file_path, "w") as f:
            f.write(content)

    def write_zip_default(self):
        zb = ProjectZipFile(response=list())
        # Default

        zb.add_response(
            self.proj_path,
            "manage.py",
            self.read_template(settings.BASE_DIR / "manage.py"),
        )
        zb.add_response(f"{self.proj_path}/templates", "meta.json", '["new"]')
        zb.add_response(f"{self.proj_path}/media", "meta.json", '["new"]')
        zb.add_response(f"{self.proj_path}/static", "meta.json", '["new"]')
        zb.add_response(
            self.interface_path,
            "asgi.py",
            self.read_template(settings.BASE_DIR / "interface" / "asgi.py"),
        )
        zb.add_response(
            self.interface_path,
            "wsgi.py",
            self.read_template(settings.BASE_DIR / "interface" / "wsgi.py"),
        )
        zb.add_response(self.interface_path, "__init__.py", "")
        return zb

    def write_zip_app(self):
        # for app in applications:
        zb = ProjectZipFile(response=list())
        # Default

        self.app_path = f"{self.proj_path}/{self.app_label}"
        zb.add_response(self.app_path, "__init__.py", "")
        zb.add_response(f"{ self.app_path}/migrations", "__init__.py", "")
        zb.add_response(f"{ self.app_path}/management", "__init__.py", "")
        zb.add_response(f"{ self.app_path}/templates", "app.html", "test")
        zb.add_response(f"{ self.app_path}/templatetags", "__init__.py", "")
        zb.add_response(f"{ self.app_path}", "apps.py", self.get_apps_template())
        zb.add_response(f"{ self.app_path}", "admin.py", self.get_admin_template())
        zb.add_response(f"{ self.app_path}", "models.py", self.get_models_template())
        zb.add_response(f"{ self.app_path}", "views.py", self.get_views_template())
        zb.add_response(
            f"{ self.app_path}", "serializers.py", self.get_serializers_template()
        )
        zb.add_response(f"{ self.app_path}", "urls.py", self.get_urls_template())
        zb.add_response(
            f"{ self.app_path}",
            "presets.py",
            self.read_template(settings.BASE_DIR / "monotremata" / "presets.py"),
        )
        zb.add_response(
            f"{ self.app_path }/management/commands",
            "setup.py",
            self.render_template(
                file_path=settings.BASE_DIR / "monotremata" / "templates" / "setup.py",
                context=self.__dict__,
            ),
        )

        return zb

    def write_zip_deployment(self, instance):
        # zb.add_response(interface_path,"settings.py",self.read_template(settings.BASE_DIR/"monotremata"/"settings.py"))
        zb = ProjectZipFile(response=list())
        for i in [["Dockerfile","Dockerfile"],["cli.sh","cli"],["docker-compose.yaml","docker_compose"]]:
            if i[1] in instance.script:
                zb.add_response(
                    self.proj_path,
                    i[0],
                    instance.script[i[1]],
                )
        return zb

    def write_zip_settings(self):
        # zb.add_response(interface_path,"settings.py",self.read_template(settings.BASE_DIR/"monotremata"/"settings.py"))
        zb = ProjectZipFile(response=list())
        self.app_labels = [i.lower() for i in self.app_labels]
        zb.add_response(
            self.interface_path,
            "settings.py",
            self.render_template(
                settings.BASE_DIR / "monotremata" / "templates" / "settings.py",
                context=self.__dict__,
            ),
        )
        zb.add_response(
            self.proj_path,
            "pyproject.toml",
            get_template("pyproject.toml").render(context=self.__dict__),
        )
        zb.add_response(
            self.interface_path,
            "urls.py",
            self.get_interface_urls_template(),
        )
        zb.add_response(
            f"{self.interface_path}/routes",
            "jwt.py",
            self.read_template(
                file_path=settings.BASE_DIR / "interface" / "routes" / "jwt.py"
            ),
        )
        zb.add_response(
            f"{self.interface_path}/routes",
            "swagger.py",
            self.read_template(
                file_path=settings.BASE_DIR / "interface" / "routes" / "swagger.py"
            ),
        )
        zb.add_response(
            f"{ self.proj_path }",
            "user.json",
            self.read_template(settings.BASE_DIR / "user.json"),
        )
        zb.add_response(
            f"{ self.proj_path }/.forgejo/workflows",
            "git-actions.yaml",
            get_template("git-actions.yaml").render(
                context={**self.__dict__, **self.kwargs}
            ),
        )
        return zb


class ModelConfigLoaderMixin:

    def get_zip(self, response=None):
        if response is None:
            response = self.load_zip()
        zb = ProjectZipFile(response=response)
        return zb


class ApplicationConfigLoader(ModelConfigLoaderMixin):
    def __init__(self, application, category="slim", **kwargs):
        self.application = application
        self.mcl: ModelConfigLoader = ModelConfigLoader
        self.category = category
        self.kwargs = kwargs

    def load_zip(self, **kwargs):
        MCLA = self.mcl(
            **{
                **self.__dict__,
                **self.kwargs,
                **kwargs,
                "app_label": self.application.name,
            },
        )
        MCLA.app_labels = [self.application.name]
        MCLA.load_from_application(self.application)
        return MCLA.write_zip_app().response


class ProjectConfigLoader(ModelConfigLoaderMixin):
    def __init__(self, project, applications=None, **kwargs):
        self.project = project
        self.applications = applications or self.project.applications.all()
        self.mcl: ModelConfigLoader = ModelConfigLoader
        self.MCL: ModelConfigLoader = None
        self.kwargs = kwargs

    def load_zip(self):
        response = list()
        self.MCL = self.mcl(
            project_folder=self.project.name, **{**self.project.__dict__, **self.kwargs}
        )
        app_labels = []
        for app in self.applications:
            app_labels.append(app.name)
            response += ApplicationConfigLoader(
                application=app,
                project_folder=self.project.name,
                **{**self.project.__dict__, **self.kwargs},
            ).load_zip(
                **self.__dict__,
            )

        self.MCL.app_labels = app_labels
        response += self.MCL.write_zip_default().response
        response += self.MCL.write_zip_settings().response
        return response


class OrganizationConfigLoader(ModelConfigLoaderMixin):
    def __init__(self, organization):
        self.organization = organization
        self.projects = self.organization.projects.all()

    def load_zip(self):
        response = list()
        for proj in self.projects:
            response += ProjectConfigLoader(
                project=proj, **{"organization_folder": self.organization.name}
            ).load_zip()
        return response


class DeploymentConfigLoader:
    def __init__(self, instance):
        self.instance = instance
        data  = {
                **instance.project.__dict__,
                "pipeline_command": instance.pipeline_command,
                "pipeline_context":{
                    "SERVICE_URL": settings.SERVICE_URL,
                    **instance.__dict__,
                    "organization": instance.organization.__dict__,
                    "project": instance.project.__dict__,
                },
            }
        self.deployment = ProjectConfigLoader(
            project=self.instance.project,
            applications=self.instance.applications.all(),
            **data
        )

    def load_zip(self):
        response = self.deployment.load_zip()
        response += self.deployment.MCL.write_zip_deployment(self.instance).response
        return response
