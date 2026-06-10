from django.core.management import call_command
from django.db import models
from monotremata.presets import PresetModelField as PF
from monotremata.presets import AbstractLifeCycleMetaModel
from django.db import transaction
from django_lifecycle import (
    hook,
    BEFORE_UPDATE,
    AFTER_UPDATE,
    BEFORE_SAVE,
    BEFORE_DELETE,
)
from monotremata.modelling import ModelConfigLoader
from django.template import Template, Context
from django.template.loader import get_template
from django.conf import settings
import collections
from datetime import datetime
from monotremata.management.commands import git
from monotremata.middleware import error_message

def appendix_file_name(instance, filename):

    return f"{instance.has_owner.username}/{filename}"


class AbstractMetaModel(AbstractLifeCycleMetaModel, models.Model):

    has_owner = PF.has_owner("abstractmetamodel_owner")

    has_members = PF.has_members("abstractmetamodel_members")

    is_private = PF.booleanfield(default=False)

    class Meta:

        abstract = True

        ordering = ["sorting"]

        app_label = "monotremata"

        verbose_name = "AbstractMetaModel"

    name = PF.namefield(max_length=254)
    tag = PF.charfield(max_length=254)
    label = PF.charfield(max_length=254)
    sorting = PF.floatfield(default=0.0)
    lifecycle_hook = PF.choices(
        [None, "default", "updated", "reload", "process", "download", "upload"]
    )
    template_string = PF.textfield()
    template_file = PF.charfield(max_length=2000)
    template_url = models.URLField(**PF.bn)
    render_from = PF.choices([None, "string", "file", "url", "default"])
    context = PF.jsonfield(default=dict)
    description = PF.textfield()

    def __str__(self):
        for i in ["fieldName", "name", "label", "tag"]:
            if hasattr(self, i):
                res = getattr(self, i)
                if res:
                    return str(res)
        return super().__str__()

    def get_admin_options(self, *args, **kwargs):
        if self.render_from in ["string"]:
            c = Context({**self.__dict__, **self.context})
            t = Template(self.template_string)
            return t.render(context=c)

    # def admin_options(self,*args,**kwargs):
    #     if kwargs.get("download") in ["string"]:
    #         x = ModelConfigLoader(project_folder=kwargs.get("project_folder",""),app_label=kwargs.get("app_label","mono"))
    #         return x.get_models_template()


class Domain(AbstractMetaModel):

    has_owner = PF.has_owner("monotremata_domain_owner")

    has_members = PF.has_members("monotremata_domain_members")

    class Meta:

        abstract = False

        ordering = ["sorting"]

        app_label = "monotremata"

        verbose_name = "🌍 Domain"
        verbose_name_plural = "🌍 Domains"

    meta = PF.jsonfield(default=dict)


class Namespace(AbstractMetaModel):

    has_owner = PF.has_owner("namespace_owner")

    has_members = PF.has_members("namespace_members")

    class Meta:

        abstract = False

        ordering = ["sorting"]

        app_label = "monotremata"

        verbose_name = "🌐 Namespace"
        verbose_name_plural = "🌐 Namespaces"

    domain = models.ForeignKey(
        "Domain",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="namespace_domain",
    )


class Organization(AbstractMetaModel):

    name = PF.namefield(max_length=254, unique=True)

    has_owner = PF.has_owner("organization_owner")

    has_members = PF.has_members("organization_members")

    class Meta:

        abstract = False

        ordering = ["sorting"]

        app_label = "monotremata"

        verbose_name = "🧭 Organization"
        verbose_name_plural = "1. 🧭 Organizations"

    domains = models.ManyToManyField(
        "Domain", blank=True, related_name="organization_domains"
    )
    namespaces = models.ManyToManyField(
        "Namespace", blank=True, related_name="organization_namespaces"
    )
    projects = models.ManyToManyField("Project", blank=True)

    @property
    def get_folder_structure():
        pass


class Project(AbstractMetaModel):
    name = PF.namefield(max_length=254, unique=True)

    db_driver = PF.choices(
        [None, "sqlite3", "spatialite", "postgres", "postgis", "cluster", "custom"]
    )
    category = PF.choices([None, "slim", "gis","server", "docker", "cluster"])

    has_owner = PF.has_owner("project_owner")

    has_members = PF.has_members("project_members")

    class Meta:

        abstract = False

        ordering = ["sorting"]

        app_label = "monotremata"

        verbose_name = "🦦 Project"
        verbose_name_plural = "2. 🦦 Projects"

    domains = models.ManyToManyField(
        "Domain", blank=True, related_name="project_domains"
    )
    namespaces = models.ManyToManyField(
        "Namespace", blank=True, related_name="project_namespaces"
    )
    applications = models.ManyToManyField("Application", blank=True)

    def get_mono_config(self):
        pass


class Application(AbstractMetaModel):
    name = PF.namefield(max_length=254, unique=True)
    has_owner = PF.has_owner("application_owner")
    has_members = PF.has_members("application_members")

    class Meta:

        abstract = False

        ordering = ["sorting"]

        app_label = "monotremata"

        verbose_name = "🦫 Application"
        verbose_name_plural = "3. 🦫 Applications"

    domains = models.ManyToManyField(
        "Domain", blank=True, related_name="application_domains"
    )
    namespaces = models.ManyToManyField(
        "Namespace", blank=True, related_name="application_namespaces"
    )
    preset_models = models.ManyToManyField("PresetModel", blank=True)


class Document(AbstractMetaModel):

    file_upload = models.FileField(upload_to=appendix_file_name)

    has_owner = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="document_owner"
    )

    has_members = PF.has_members("document_members")

    class Meta:

        abstract = False

        ordering = ["sorting"]

        app_label = "monotremata"

        verbose_name = "📑 Document"
        verbose_name_plural = "📑 Documents"

    domains = models.ManyToManyField(
        "Domain", blank=True, related_name="document_domains"
    )
    namespaces = models.ManyToManyField(
        "Namespace", blank=True, related_name="document_namespaces"
    )
    file_size = PF.floatfield()
    file_format = PF.charfield()
    uploaded = models.DateTimeField(auto_now=True)
    sheet_name = PF.charfield(max_length=500)
    sheet_names = PF.jsonfield()
    label = PF.charfield(max_length=254, kwargs={})
    lifecycle_hook = PF.choices(
        [None, "updated", "process"]
    )
    @hook(AFTER_UPDATE)
    def parse_upload_model_fields(self):
        if self.lifecycle_hook in ["process"]:
            self.set_info()
            self.lifecycle_hook = "updated"
            # call_command("parser","-ids",self.id)
            transaction.on_commit(lambda: call_command("parser", "-ids", self.id))
            self.save()


    def set_info(self):
        if self.lifecycle_hook in ["process"]:
            self.lifecycle_hook = "updated"
            if self.file_upload and self.file_upload.file:
                self.file_format = self.file_upload.file.name.split(".")[-1]
                self.file_size = self.file_upload.file.size
            self.save()


class PresetModel(AbstractMetaModel):

    has_owner = PF.has_owner("presetmodel_owner")

    has_members = PF.has_members("presetmodel_members")

    class Meta:

        abstract = False

        ordering = ["sorting"]

        app_label = "monotremata"

        verbose_name = "🦔 Model"
        verbose_name_plural = "5. 🦔 Model"

        unique_together = ["name", "has_owner", "tag"]

    domains = models.ManyToManyField("Domain", blank=True, related_name="model_domains")
    namespaces = models.ManyToManyField(
        "Namespace", blank=True, related_name="model_namespaces"
    )
    className = PF.classnamefield(kwargs={}, default="Organization")
    classParent = PF.classnamefield(kwargs={}, default="models.Model")
    fields = models.ManyToManyField("PresetModelField", blank=True)
    is_abstract = PF.booleanfield(default=False)
    ordering_list = PF.jsonfield()
    app_label = PF.charfield()
    verbose_name = PF.charfield()
    verbose_name_plural = PF.charfield()
    serializerClassParent = PF.classnamefield(default="serializers.ModelSerializer")
    viewsetClassParent = PF.classnamefield(default="viewsets.ModelViewSet")
    permissionClasses = PF.classnamefield()
    querysetString = PF.charfield(max_length=1000)
    filterFields = PF.jsonfield()
    searchFields = PF.jsonfield()


class PresetModelField(AbstractMetaModel):

    has_owner = PF.has_owner("presetmodelfield_owner")

    has_members = PF.has_members("presetmodelfield_members")

    class Meta:

        abstract = False

        ordering = ["sorting"]

        app_label = "monotremata"

        verbose_name = "🦆 Model Field"
        verbose_name_plural = "6. 🦆 Model Fields"

        unique_together = [
            "name",
            "has_owner",
            "tag",
            "fieldName",
            "fieldDataType",
            "fieldParameters",
        ]

    domains = models.ManyToManyField("Domain", blank=True, related_name="field_domains")
    namespaces = models.ManyToManyField(
        "Namespace", blank=True, related_name="field_namespaces"
    )
    fieldDataType = PF.choices(PF.field_classes)
    fieldName = PF.namefield()
    fieldParameters = PF.textfield(default="**PF.bn")
    valid_name = PF.booleanfield(default=False)
    error_message = PF.jsonfield()


class Deployment(AbstractMetaModel):
    name = PF.namefield(max_length=254,kwargs={})
    is_private = PF.booleanfield(default=True)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE)
    namespace = models.ForeignKey(Namespace, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    applications = models.ManyToManyField(Application)
    lifecycle_hook = PF.choices(
        [None, "reload", "test", "deploy", "stop", "start", "update", "delete"]
    )
    framework = PF.choices(
        [
            None,
            "applicationset.yaml",
            "Dockerfile",
            "docker-compose.yaml",
            "manifest.yaml",
            "cli.sh",
            "fixed.sys",
        ]
    )
    script = PF.map_dict()
    service_public_url = models.URLField()
    service_private_url = models.URLField()
    helm_repository = models.URLField(
        default=f"{ settings.GIT_HOST }/amir/clustermanager.git"
    )
    helm_repository_branch = PF.charfield(default="main")
    git_api_url = models.URLField(**PF.bn)
    git_organization_username = PF.namefield()
    git_organization_password = PF.passwordfield(kwargs={})

    db_user = PF.namefield(kwargs={})
    db_name = PF.namefield(kwargs={})
    db_host = PF.charfield(
        default="ge-postgres.database.svc.cluster.local", max_length=2000, kwargs={}
    )
    db_port = PF.integerfield(default=5432, kwargs={})
    db_password = PF.passwordfield(kwargs={})
    container_command = PF.textfield()
    pipeline_command = PF.jsonfield()
    registry_url = PF.charfield(max_length=2000, default="localhost:32000", kwargs={})
    git_token = PF.charfield(max_length=2000)
    jupyter_token = PF.charfield(max_length=2000)

    @property
    def meta_name(self):
        return f"vo{self.id}ov{str(self.organization.name)}{str(self.project.name)}"

    class Meta:

        abstract = False

        ordering = ["sorting"]

        app_label = "monotremata"

        verbose_name = "🥚 Deployment"
        verbose_name_plural = "7. 🥚 Deployments"

        unique_together = [
            "name",
            "has_owner",
            "tag",
            "domain",
            "namespace",
            "organization",
            "project",
        ]

    def get_reporting(self):
        return {"updated": str(datetime.now())}

    @hook(BEFORE_SAVE)
    @hook(BEFORE_UPDATE)
    def lifecycle(self):
        try:
            # get template and render to script
            if self.framework is None or self.lifecycle_hook in ["reload"]:
                for i in [
                    "cli.sh",
                    "Dockerfile",
                    "applicationset.yaml",
                    "docker-compose.yaml",
                ]:
                    self.framework = i
                    self.update_script()
                    self.script["report"] = {"created": str(datetime.now())}
            elif self.framework not in ["fixed.sys", None]:
                self.update_script()
                if "report" in self.script:
                    if self.get_framework_name() in self.script["report"]:
                        self.script["report"][self.get_framework_name()].append(
                            self.get_reporting()
                        )
                    else:
                        self.script["report"][self.get_framework_name()] = [
                            self.get_reporting()
                        ]
                else:
                    self.script["report"] = {
                        self.get_framework_name(): [self.get_reporting()]
                    }
                    self.script = collections.OrderedDict(
                        sorted(self.script.items(), reverse=True)
                    )

            self.api_git_generate_access_token()
            self.api_git_create_organization()
            self.api_git_create_repository()
            self.git_manage_repository()
            self.lifecycle_hook = "updated"
            self.framework = "fixed.sys"
        except Exception as e:
            error_message(e)

    def git_api_client(self):
        if not self.git_api_url:
            self.git_api_url = settings.GIT_URL
        return git.GitApi(
            username=self.git_organization_username,
            password=self.git_organization_password,
            organization=self.organization,
            deployment=self,
            GIT_URL=self.git_api_url,
            token=self.git_token,
        )

    def api_git_generate_access_token(self):
        if self.lifecycle_hook in ["deploy"] and not self.git_token:
            api = self.git_api_client()
            token = api.create_access_token()
            if token:
                self.git_token = token

    def api_git_create_organization(self):
        if self.lifecycle_hook in ["deploy"]:
            api = self.git_api_client()
            api.create_organization()

    def api_git_create_repository(self):
        if self.lifecycle_hook in ["deploy"]:
            api = self.git_api_client()
            api.create_repository()

    def git_manage_repository(self):
        if self.lifecycle_hook in ["deploy"]:
            api = self.git_api_client()
            response = api.write_project_zip_to_repository()
            
            if isinstance(response,list) and "no-token-set" in response:
               response = self.api_git_generate_access_token()
               if isinstance(response,list) and "no-token-set" not in  response:
                   response = api.write_project_zip_to_repository()


    @hook(BEFORE_DELETE)
    def api_git_delete_organization(self):
        api = self.git_api_client()
        api.delete_access_token()
        api.delete_repository()
        api.delete_organization()

    def get_framework_name(self):
        return str(self.framework).split(".")[0].replace("-", "_")

    def update_script(self):
        if not self.script:
            self.script = {}
        tmp = None
        if self.framework:
            tmp = get_template(self.framework)

        if tmp:
            context = {
                **self.__dict__,
                "has_owner": self.has_owner.username,
                "SERVICE_URL": settings.SERVICE_URL,
                "SERVICE_HOST": settings.SERVICE_HOST,
                "GIT_URL": settings.GIT_URL,
                "GIT_HOST": settings.GIT_HOST,
                "meta_name": self.meta_name,
                "organization": self.organization.__dict__,
                "project": self.project.__dict__,
                "service_public_url": f"{self.service_public_url}".replace(
                    "http://", ""
                ).replace("https://", ""),
                "service_private_url": f"{self.service_public_url}".replace(
                    "http://", ""
                ).replace("https://", ""),
            }

            self.script[self.get_framework_name()] = tmp.render(context=context)
