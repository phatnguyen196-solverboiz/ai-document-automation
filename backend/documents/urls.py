from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet, ProcessingJobViewSet

router = DefaultRouter()
router.register("documents", DocumentViewSet, basename="document")
router.register("jobs", ProcessingJobViewSet, basename="job")

urlpatterns = router.urls
