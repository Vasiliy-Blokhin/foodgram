from django_filters import filters
from django_filters.rest_framework import FilterSet
from rest_framework.filters import SearchFilter

from main.models import Recipe, Tag, User


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(field_name='tags__slug',
                                             queryset=Tag.objects.all(),
                                             to_field_name='slug')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.id:
            return queryset.filter(recipe_favorite__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.id:
            return queryset.filter(recipe_shop__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        author = User
        fields = ['tags', 'author']


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'
