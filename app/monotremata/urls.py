from rest_framework.routers import DefaultRouter

from monotremata import views

router = DefaultRouter()


router.register("organization", views.OrganizationModelViewSet, basename="organization")
router.register("project", views.ProjectModelViewSet, basename="project")
router.register("application", views.ApplicationModelViewSet, basename="application")
router.register("domain", views.DomainModelViewSet, basename="domain")
router.register("namespace", views.NamespaceModelViewSet, basename="namespace")
router.register("presetmodel", views.PresetModelModelViewSet, basename="presetmodel")
router.register(
    "presetmodelfield", views.PresetModelFieldModelViewSet, basename="presetmodelfield"
)
router.register("deployment", views.DeploymentModelViewSet, basename="deployment")
router.register("site", views.SiteModelViewSet, basename="site")
router.register("flatpage", views.FlatPageModelViewSet, basename="flatpage")
urlpatterns = router.urls
