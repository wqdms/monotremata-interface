from rest_framework import serializers
from django.contrib.sites.models import Site
from django.contrib.flatpages.models import FlatPage
from monotremata import models

class FlatPageModelSerializer(serializers.ModelSerializer):

    class Meta:

        model = FlatPage

        fields = "__all__"

class SiteModelSerializer(serializers.ModelSerializer):

    class Meta:

        model = Site

        fields = "__all__"



class NamespaceModelSerializer(serializers.ModelSerializer):

    class Meta:

        model = models.Namespace

        fields = "__all__"


class PresetModelFieldModelSerializer(serializers.ModelSerializer):

    class Meta:

        model = models.PresetModelField

        fields = "__all__"


class PresetModelModelSerializer(serializers.ModelSerializer):
    fields = PresetModelFieldModelSerializer(read_only=True, many=True)

    class Meta:

        model = models.PresetModel

        fields = "__all__"


class ApplicationModelSerializer(serializers.ModelSerializer):
    preset_models = PresetModelModelSerializer(read_only=True, many=True)

    class Meta:

        model = models.Application

        fields = "__all__"


class ProjectModelSerializer(serializers.ModelSerializer):
    applications = ApplicationModelSerializer(read_only=True, many=True)

    class Meta:

        model = models.Project

        fields = "__all__"


class OrganizationModelSerializer(serializers.ModelSerializer):

    projects = ProjectModelSerializer(read_only=True, many=True)

    class Meta:

        model = models.Organization

        fields = "__all__"


class DomainModelSerializer(serializers.ModelSerializer):

    class Meta:

        model = models.Domain

        fields = "__all__"


class DeploymentModelSerializer(serializers.ModelSerializer):

    class Meta:

        model = models.Deployment

        fields = ["script"] + [
            i.name
            for i in models.Deployment._meta.get_fields()
            if i.name not in ["script"]
        ]
        extra_kwargs = {
            "db_password": {
                "write_only": True,  # Hidden from API responses
                "style": {"input_type": "password"},  # Hidden in Browsable API UI
            }
        }
