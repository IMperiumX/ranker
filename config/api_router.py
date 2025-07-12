from django.conf import settings
from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from ranker.games.api.views import GameViewSet
from ranker.users.api.views import UserViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)
router.register("games", GameViewSet)


app_name = "api"
urlpatterns = router.urls + [
    # Include scores app URLs
    path("", include("ranker.scores.urls")),
]
