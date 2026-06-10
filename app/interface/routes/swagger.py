from django.urls import path
from drf_spectacular.views import (
    SpectacularSwaggerView,
    SpectacularJSONAPIView,
)

urlpatterns = [
    path(
        "swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger",
    ),
    path(
        "schema/",
        SpectacularJSONAPIView().as_view(),
        name="schema",
    ),
]
