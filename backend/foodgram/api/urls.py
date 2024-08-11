from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (
    FavoriteViewSet,
    IngredientViewSet,
    ProfileViewSet,
    RecipeViewSet,
    RedirectShortUrl,
    ShopListViewSet,
    SubscribeViewSet,
    TagViewSet,
    TokenViewSet,
)
from foodgram.constants import SHORT_URL_SPLIT


router = DefaultRouter()

router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('auth/token', TokenViewSet)
router.register('users', ProfileViewSet)


urlpatterns = [
    path(
        SHORT_URL_SPLIT + '<slug:slug>/',
        RedirectShortUrl
    ),
    path(
        'user/<int:pk>/subscribe/',
        SubscribeViewSet.as_view({"post": "create", "delete": "destroy"})
    ),
    path(
        'user/subscriptions/',
        SubscribeViewSet.as_view({"get": "list", })
    ),
    path(
        'recipes/<int:pk>/favorite/',
        FavoriteViewSet.as_view({
            "post": "create",
            "delete": "destroy"
        })
    ),
    path(
        'recipes/download_shopping_cart/',
        ShopListViewSet.as_view({"get": "list", })
    ),
    path(
        'recipes/<int:pk>/shopping_cart/',
        ShopListViewSet.as_view({"post": "create", "delete": "destroy"})
    ),
    path('', include(router.urls)),
]
