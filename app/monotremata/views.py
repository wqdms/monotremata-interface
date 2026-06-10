from __future__ import annotations
from monotremata import admin
from types import SimpleNamespace
from monotremata import serializers


from rest_framework import (
    permissions,
    viewsets,
    renderers,
    filters,
)
from django_filters.rest_framework import DjangoFilterBackend


from django.db.models import Q

from monotremata import serializers


class DownloadRenderer(renderers.BrowsableAPIRenderer):
    format = "download"
    media_type = "application/octet-stream"


DEFAULT_RENDERERS = [
    renderers.BrowsableAPIRenderer,
    renderers.JSONRenderer,
    renderers.AdminRenderer,
]

DEFAULT_PERMISSIONS = [permissions.IsAuthenticatedOrReadOnly]


def set_filterset_fields_exclude(serializer_class):
    fields = [
        "JSONField",
        "PointField",
        "MultiPointField",
        "PolygonField",
        "MultiPolygonField",
        "LineStringField",
        "MultiLineStringField",
        "GenericForeignKey",
        "FileField",
        "CompositePrimaryKey",
        "GeometryField",
        "ForeignKey",
        "OneToOneField",
        "ManyToManyField",
        "ManyToManyRel",
        "ManyToOneRel",
    ]
    result = []
    for field in serializer_class.Meta.model._meta.get_fields():
        if field.__class__.__name__ not in fields:
            result.append(field.name)

    return result


class ApplicationSlimRenderer(renderers.BrowsableAPIRenderer):
    format = "slim"


class MetaQuerySetMixin:
    def get_queryset(self):
        if self.request.user.is_superuser:
            qs = self.serializer_class.Meta.model.objects.all()
        elif self.request.user.is_authenticated:
            qs = self.serializer_class.Meta.model.objects.filter(
                Q(
                    Q(has_owner=self.request.user)
                    | Q(has_members__in=[self.request.user])
                    | Q(is_private=False)
                )
            )
        else:
            qs = self.serializer_class.Meta.model.objects.filter(is_private=False)
        return qs


class MetaViewset(MetaQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = None
    permission_classes = DEFAULT_PERMISSIONS
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    renderer_classes = DEFAULT_RENDERERS

    def get_renderer_context(self):
        ctx = super().get_renderer_context()
        ctx["model_name"] = self.serializer_class.Meta.model.__name__
        return ctx


class DownloadViewMixin:
    def get_download(self, response):
        if self.request.GET.get("format") in ["download"]:
            m = SimpleNamespace(model=self.serializer_class.Meta.model)
            return admin.download_zip(
                modeladmin=m,
                request=self.request,
                queryset=self.filter_queryset(self.get_queryset()),
            )
        return response

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return self.get_download(response)

    def retrieve(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return self.get_download(response)


class DomainModelViewSet(MetaViewset):

    serializer_class = serializers.DomainModelSerializer
    queryset = serializer_class.Meta.model.objects.all()
    permission_classes = DEFAULT_PERMISSIONS


class NamespaceModelViewSet(MetaViewset):

    serializer_class = serializers.NamespaceModelSerializer

    queryset = serializer_class.Meta.model.objects.all()

    permission_classes = DEFAULT_PERMISSIONS


class OrganizationModelViewSet(DownloadViewMixin, MetaViewset):

    serializer_class = serializers.OrganizationModelSerializer

    queryset = serializer_class.Meta.model.objects.all()

    renderer_classes = [*DEFAULT_RENDERERS, DownloadRenderer]
    permission_classes = DEFAULT_PERMISSIONS
    filterset_fields = [
        "id",
        "name",
        "tag",
        "label",
        "projects__name",
        "projects__tag",
        "projects__label",
        "projects__applications__name",
        "projects__applications__tag",
        "projects__applications__label",
    ]
    search_fields = filterset_fields


class ProjectModelViewSet(DownloadViewMixin, MetaViewset):

    serializer_class = serializers.ProjectModelSerializer
    renderer_classes = [*DEFAULT_RENDERERS, DownloadRenderer]
    queryset = serializer_class.Meta.model.objects.all()
    permission_classes = DEFAULT_PERMISSIONS
    filterset_fields = [
        "id",
        "name",
        "tag",
        "label",
        "applications__name",
        "applications__tag",
        "applications__label",
    ]
    search_fields = filterset_fields


class ApplicationModelViewSet(DownloadViewMixin, MetaViewset):

    serializer_class = serializers.ApplicationModelSerializer
    renderer_classes = [*DEFAULT_RENDERERS, DownloadRenderer]
    queryset = serializer_class.Meta.model.objects.all()
    permission_classes = DEFAULT_PERMISSIONS
    filterset_fields = [
        "id",
        "name",
        "tag",
        "label",
        "preset_models__name",
        "preset_models__tag",
        "preset_models__label",
    ]
    search_fields = filterset_fields


class PresetModelModelViewSet(MetaViewset):

    serializer_class = serializers.PresetModelModelSerializer
    renderer_classes = [*DEFAULT_RENDERERS, DownloadRenderer]
    queryset = serializer_class.Meta.model.objects.all()
    permission_classes = DEFAULT_PERMISSIONS
    filterset_fields = [
        "id",
        "name",
        "tag",
        "label",
        "classParent",
        "className",
        "fields__name",
        "fields__tag",
        "fields__label",
        "fields__fieldName",
        "fields__fieldDataType",
        "fields__valid_name",
    ]
    search_fields = filterset_fields


class PresetModelFieldModelViewSet(MetaViewset):

    serializer_class = serializers.PresetModelFieldModelSerializer

    queryset = serializer_class.Meta.model.objects.all()
    permission_classes = DEFAULT_PERMISSIONS


class DeploymentModelViewSet(DownloadViewMixin, MetaViewset):

    serializer_class = serializers.DeploymentModelSerializer
    renderer_classes = [*DEFAULT_RENDERERS, DownloadRenderer]
    queryset = serializer_class.Meta.model.objects.all()
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = [
        "id",
        "name",
        "tag",
        "label",
        "organization__name",
        "project__name",
        "applications__name",
        "applications__tag",
        "applications__label",
    ]
    search_fields = filterset_fields


class FlatPageModelViewSet(viewsets.ModelViewSet):

    serializer_class = serializers.FlatPageModelSerializer

    queryset = serializer_class.Meta.model.objects.all()

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SiteModelViewSet(viewsets.ModelViewSet):

    serializer_class = serializers.SiteModelSerializer

    queryset = serializer_class.Meta.model.objects.all()

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]