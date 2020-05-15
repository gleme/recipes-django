from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipes.views import TagViewSet, IngredientViewSet

router = DefaultRouter()
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)

app_name = 'recipes'

urlpatterns = [
    path('', include(router.urls))
]
