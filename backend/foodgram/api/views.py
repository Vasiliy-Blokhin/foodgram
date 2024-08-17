import io

from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response

from api.serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    ProfileSerializer,
    PasswordSerializer,
    RecipeCreateSerializer,
    RecipeSerializer,
    RecipeShopSerializer,
    SubscribeSerializer,
    SignupSerializer,
    TagSerializer,
    TokenSerializer
)
from api.filter import IngredientSearchFilter, RecipeFilter
from api.pagination import PagePagination
from api.permissions import IsAuthenticatedAndOwner
from main.constants import RECIPE_URL, START_URL
from main.models import (
    Follow,
    Ingredient,
    Recipe,
    RecipeFavorite,
    RecipeIngredient,
    RecipeShop,
    ShortUrl,
    Tag,
    User
)


@action(methods=['get', 'post', 'patch', 'delete'], detail=True)
class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-pub_date')
    ordering_fields = ['pub_date']
    ordering = ['-pub_date']
    serializer_class = RecipeSerializer
    filter_backends = [DjangoFilterBackend, ]
    filter_class = RecipeFilter
    pagination_class = PagePagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'request': self.request,
        })
        if self.kwargs.get('pk'):
            context.update({"id": self.kwargs.get('pk')})
        return context

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    @action(
        methods=('GET',),
        detail=True,
        permission_classes=(permissions.AllowAny,),
        url_path='get-link'
    )
    def get_link(self, request, pk):
        if len(ShortUrl.objects.filter(recipe_id=pk)):
            short_url = ShortUrl.objects.get(recipe_id=pk).short_url
        else:
            short_url = ShortUrl.generate()
            ShortUrl.objects.create(
                recipe_id=pk,
                short_url=short_url
            )
        short_url = START_URL + short_url
        return Response(
            {'short-link': short_url},
            status=status.HTTP_201_CREATED
        )


@action(
    methods=('GET',),
    detail=True,
    permission_classes=(permissions.AllowAny,),
)
def RedirectShortUrl(request, slug):
    recipe_id = get_object_or_404(
        ShortUrl,
        short_url=ShortUrl.find_slug(slug)
    )
    return redirect(RECIPE_URL + str(recipe_id.recipe_id))


@action(methods=['get', ], detail=True)
class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [IngredientSearchFilter, ]
    search_fields = ('name',)
    pagination_class = None


@action(methods=['get', ], detail=True)
class TagViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


@action(
    methods=['get', 'post', 'put', 'delete'],
    detail=True
)
class ProfileViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    filter_backends = [DjangoFilterBackend, ]

    def get_serializer_class(self):
        if self.action in ('create',):
            return SignupSerializer
        return ProfileSerializer

    @action(
        methods=['get', ],
        detail=False,
        url_path='me',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        methods=['put', 'delete', ],
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = self.request.user
        if request.method == 'PUT':
            request.data['email'] = user.email
            request.data['username'] = user.username
            serializer = self.get_serializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': 'change success.'},
                status=status.HTTP_200_OK
            )
        user.avatar.delete()
        user.save()
        return Response(
            {'avatar': 'delete success.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(methods=['post', ], detail=False, url_path='set_password')
    def set_password(self, request):
        serializer = PasswordSerializer(
            data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@action(methods=['get', 'post', 'delete', ], detail=True,)
class SubscribeViewSet(viewsets.ModelViewSet):
    serializer_class = SubscribeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.data.get('recipes_limit'):
            recipes_limit = self.request.data['recipes_limit']
        else:
            recipes_limit = None
        context.update({
            'request': self.request,
            'recipes_limit': recipes_limit,
        })
        if self.kwargs.get('pk'):
            context.update({'pk': self.kwargs.get('pk')})
        return context

    def get_follow(self):
        return Follow.objects.filter(user=self.request.user)

    def get_queryset(self):
        if self.action in ('create',):
            return User.objects.all()
        return User.objects.filter(
            following__in=self.get_follow()
        ).distinct()

    def destroy(self, request, *args, **kwargs):
        author = get_object_or_404(User, id=self.kwargs.get('pk'))
        user = request.user
        get_object_or_404(Follow, author=author, user=user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@action(methods=[], detail=False)
class TokenViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = TokenSerializer

    @action(
        methods=['post', ], detail=False, url_path='login',
        permission_classes=[permissions.AllowAny]
    )
    def login(self, request):
        serializer = TokenSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        token = serializer.save()
        return Response(
            {'auth_token': token.key},
            status=status.HTTP_201_CREATED
        )

    @action(
        methods=['post', ], detail=False, url_path='logout',
        permission_classes=[permissions.IsAuthenticated]
    )
    def logout(self, request):
        user = request.user
        Token.objects.get(user=user).delete()
        data = {
            'detail': 'Токен удален.'
        }
        return Response(data, status=status.HTTP_204_NO_CONTENT)


@action(methods=['post', 'delete', ], detail=True)
class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        if self.action in ('create',):
            return RecipeFavorite.objects.all()
        return RecipeFavorite.filter(
            user=self.request.user
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'request': self.request,
        })
        if self.kwargs.get('pk'):
            context.update({'pk': self.kwargs.get('pk')})
        return context

    def destroy(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        user = self.request.user
        get_object_or_404(RecipeFavorite, recipe=recipe, user=user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@action(
    methods=['get', 'post', 'delete', ],
    permission_classes=(IsAuthenticatedAndOwner,),
    detail=True)
class ShopListViewSet(FavoriteViewSet):
    serializer_class = RecipeShopSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'request': self.request,
        })
        if self.kwargs.get('pk'):
            context.update({'pk': self.kwargs.get('pk')})
        return context

    @staticmethod
    def shop_text(self, user):
        ingredient_list = RecipeIngredient.objects.filter(
            recipe__recipe_shop__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(count=Sum('amount'))
        text = ['Корзина покупок:']
        for index, recipe_ingredient in enumerate(ingredient_list):
            name = recipe_ingredient.recipe.name
            measurement_unit = recipe_ingredient.ingredient.measurement_unit
            count = recipe_ingredient.amount
            ingredient = (
                f'\n{index}. {name} -'
                f'{count} {measurement_unit}.'
            )
            text.append(ingredient)
        return ' '.join(text)

    def list(self, request, *args, **kwargs):
        buffer = io.StringIO()
        buffer.write(
            self.shop_text(self, request.user)
        )
        response = FileResponse(buffer.getvalue(), content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response

    def destroy(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        user = self.request.user
        get_object_or_404(RecipeShop, recipe=recipe, user=user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
