import re
from os import getenv
from django.contrib import admin
from django.db import models
from django.core import validators
from django.utils.regex_helper import _lazy_re_compile
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from import_export.admin import ImportExportModelAdmin
from django_lifecycle import (
    LifecycleModelMixin,
    hook,
    BEFORE_UPDATE,
    AFTER_UPDATE,
    BEFORE_SAVE,
    AFTER_SAVE,
    AFTER_CREATE,
    BEFORE_CREATE,
)
from django.conf import settings
from django import forms

SET_GIS = False
if settings.DATABASE_ENGINE not in ["sqlite3"]:
    SET_GIS = True
    from django.contrib.gis.db import models as gis_models


def is_numeric_value(s):
    # This regex looks for an optional minus sign,
    # followed by a digit OR a decimal point and a digit

    is_num = bool(re.match(r"^-?\d|^-?\.\d", s))
    return is_num


def validate_is_not_numeric_value(s):
    if is_numeric_value(s):
        raise ValidationError(f"{s} can not start with a numeric value")


name_re = _lazy_re_compile(r"^[a-zA-Z0-9_]+\Z")
validate_name = validators.RegexValidator(
    name_re,
    # Translators: "letters" means latin letters: a-z and A-Z.
    _("Enter a valid “name” consisting of letters, numbers, underscores."),
    "invalid",
)


class_re = _lazy_re_compile(r"^[a-zA-Z0-9._]+\Z")
validate_class = validators.RegexValidator(
    class_re,
    # Translators: "letters" means latin letters: a-z and A-Z.
    _(
        "Enter a valid “class string” consisting of letters, numbers, underscores and dots."
    ),
    "invalid",
)


def get_field_classes_from_module(module_name="models", module=models):
    return [
        f"{module_name}.{name}"
        for name in dir(module)
        if isinstance(getattr(module, name), type)
        and (name.endswith("Field") or name == "ForeignKey")
        and not name.startswith("_")
    ]


def get_field_classes(field_classes_default, field_classes_gis=None):
    names = [n.split(".")[-1] for n in field_classes_default]
    reset_gis = []
    field_classes = field_classes_default + reset_gis
    if field_classes_gis:
        for i in field_classes_gis:
            name = i.split(".")[-1]
            if name not in names:
                reset_gis.append(i)
        field_classes += reset_gis
    options = [
        "choices",
        "charfield",
        "textfield",
        "has_owner",
        "has_members",
        "classnamefield",
        "namefield",
        "jsonfield",
        "floatfield",
        "integerfield",
        "booleanfield",
        "map_float64",
        "map_int64",
        "map_str",
        "map_object",
        "map_list",
        "map_dict",
        "map_bool",
        "geojson"
    ]
    if SET_GIS:
        options.append("geometrycollectionfield")
    return sorted(
        field_classes + [f"Preset.{i}" for i in options],
    )


field_classes_default = get_field_classes_from_module("models", models)
field_classes_gis = None
if SET_GIS:
    field_classes_gis = get_field_classes_from_module("gis_models", gis_models)

FIELD_CLASSES = get_field_classes(
    field_classes_default=field_classes_default, field_classes_gis=field_classes_gis
)


class EncryptedPasswordField(models.CharField):
    """
    A field that automatically uses a PasswordInput widget in forms.
    """

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 128  # Standard for hashed passwords
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        # This forces the Django Admin and ModelForms to use <input type="password">
        defaults = {"widget": forms.PasswordInput}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class PresetModelField:
    field_classes = FIELD_CLASSES
    bn: dict = {"blank": True, "null": True}
    passwordfield: EncryptedPasswordField = lambda kwargs=bn: EncryptedPasswordField(
        **kwargs
    )
    charfield: models.CharField = (
        lambda max_length=254, unique=False, help_text=None, default=None, kwargs=bn: models.CharField(
            max_length=max_length,
            unique=unique,
            help_text=help_text,
            default=default,
            **kwargs,
        )
    )
    textfield: models.TextField = (
        lambda default=None, help_text=None, kwargs=bn: models.TextField(
            default=default, help_text=help_text, **kwargs
        )
    )

    floatfield: models.FloatField = (
        lambda default=0.0, help_text=None, kwargs=bn: models.FloatField(
            default=default, help_text=help_text, **kwargs
        )
    )
    integerfield: models.IntegerField = (
        lambda default=0, help_text=None, kwargs=bn: models.IntegerField(
            default=default, help_text=help_text, **kwargs
        )
    )
    jsonfield: models.JSONField = (
        lambda default=list, help_text=None, kwargs=bn: models.JSONField(
            default=default, help_text=help_text, **kwargs
        )
    )
    geojsonfield: models.JSONField = (
        lambda default=list, help_text=None, kwargs=bn: models.JSONField(
            default=default, help_text=help_text, **kwargs
        )
    )
    map_dict: models.JSONField = (
        lambda default=dict, help_text=None, kwargs=bn: models.JSONField(
            default=default, help_text=help_text, **kwargs
        )
    )
    booleanfield: models.BooleanField = (
        lambda default=True, help_text=None, kwargs=bn: models.BooleanField(
            default=default, help_text=help_text, **kwargs
        )
    )
    namefield: models.CharField = (
        lambda max_length=254, unique=False, help_text=None, kwargs=bn: models.CharField(
            max_length=max_length,
            unique=unique,
            help_text=help_text,
            validators=[validate_name],
            **kwargs,
        )
    )
    classnamefield: models.CharField = (
        lambda max_length=254, default="models.Model", unique=False, help_text=None, kwargs=bn: models.CharField(
            max_length=max_length,
            unique=unique,
            help_text=help_text,
            validators=[validate_class],
            default=default,
            **kwargs,
        )
    )
    has_owner: models.ForeignKey = lambda related_name, kwargs=bn: models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, related_name=related_name, **kwargs
    )
    has_members: (
        models.ManyToManyField
    ) = lambda related_name, blank=True, kwargs={}: models.ManyToManyField(
        "auth.User", related_name=related_name, blank=blank, **kwargs
    )
    choices: models.CharField = (
        lambda array, max_length=100, default=None, help_text=None, kwargs=bn: models.CharField(
            max_length=max_length,
            choices=[[i, i] for i in array],
            help_text=help_text,
            default=default,
            **kwargs,
        )
    )
    map_float64 = floatfield
    map_int64 = integerfield
    map_str = textfield
    map_object = map_dict
    map_list = jsonfield
    map_bool = booleanfield
    if SET_GIS:
        geometrycollectionfield = lambda kwargs: gis_models.GeometryCollectionField(**bn,**kwargs)

class AbstractMetaModelMixin:

    def lifecycle(self):
        return True


class AbstractMetaModel:
    class Meta:
        abstract: bool = True


class AbstractLifeCycleMetaModel(
    LifecycleModelMixin, AbstractMetaModelMixin, models.Model
):
    class Meta:
        abstract: bool = True


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


def load_dynamic_admin(app_models):

    exclude_list = ["id"]

    for model in app_models:
        # Create a dynamic Admin class
        class DynamicAdmin(ImportExportModelAdmin):
            actions = []
            if "is_private" in [i.name for i in model._meta.fields]:
                actions = [set_private, unset_private]
            list_filter = [
                field.name
                for field in model._meta.fields
                if field.name not in [*exclude_list, "name"]
            ]
            verbose_name = model.__name__
            list_display = [
                field.name
                for field in model._meta.fields
                if field.name not in exclude_list
            ]
            readonly_fields = ["id"]

            def get_readonly_fields(self, request, obj=None):
                if hasattr(obj, "has_owner") and not request.user.is_superuser:
                    return self.readonly_fields + ["has_owner"]
                if hasattr(obj, "file"):
                    return self.readonly_fields + ["file", "format", "size"]
                return self.readonly_fields

            def save_model(self, request, obj, form, change):
                if hasattr(obj, "has_owner"):
                    if not obj.has_owner:
                        obj.has_owner = request.user
                super().save_model(request, obj, form, change)

        try:
            admin.site.register(model, DynamicAdmin)
        except admin.sites.AlreadyRegistered:
            pass
    return admin
