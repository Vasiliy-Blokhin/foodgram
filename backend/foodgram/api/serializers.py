from drf_extra_fields.fields import Base64ImageField
from django.core.exceptions import ValidationError
from django.core.validators import (
    EmailValidator,
    MaxValueValidator,
    MinValueValidator
)
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from main.constants import (
    MAX_AMOUNT,
    MIN_AMOUNT
)
from main.models import (
    Follow,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeShop,
    RecipeTag,
    RecipeFavorite,
    Tag,
    User
)


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=(EmailValidator,))
    username = serializers.CharField()
    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField(required=False)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        is_user = request and request.user.id
        return is_user and Follow.objects.filter(
            author=obj,
            user=request.user
        ).exists()


class SignupSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=(EmailValidator,)
    )
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=150, write_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'password'
        )


class TokenSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=(EmailValidator,),
        write_only=True
    )
    password = serializers.CharField(write_only=True)
    auth_token = serializers.SerializerMethodField(
        read_only=True,
        required=False
    )

    class Meta:
        model = Token
        fields = (
            'email', 'password', 'auth_token'
        )

    @staticmethod
    def get_user_email(self, email):
        return get_object_or_404(
            User, email=email
        )

    def get_auth_token(self, obj):
        request = self.context.get('request')
        if request.data.get('email') and request.data.get('password'):
            user = self.get_user_email(
                self,
                request.data['email']
            )
            if user.check_password(request.data['password']):
                return Token.objects.get(user=user).key

    def create(self, validated_data):
        user = self.get_user_email(
            self,
            validated_data.get('email')
        )
        if user.check_password(validated_data.get('password')):
            obj, created = Token.objects.get_or_create(user=user)
            return obj


class PasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.SerializerMethodField()
    current_password = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'new_password', 'current_password'
        )

    def get_new_password(self, obj):
        request = self.context.get('request')
        if request.data.get('new_password'):
            return request.data.get('new_password')

    def get_current_password(self, obj):
        request = self.context.get('request')
        if request.data.get('current_password'):
            return request.data.get('current_password')

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        if user.check_password(validated_data['current_password']):
            user.set_password(validated_data['new_password'])
            user.save()
            return user


class TagSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = Tag
        fields = (
            'id', 'name', 'slug'
        )


class TagIdSerializer(serializers.ListField):

    class Meta:
        model = Tag
        fields = ('id',)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = (
            'id', 'name', 'measurement_unit'
        )


class IngredientCreateSerializer(serializers.Serializer):
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT)
        ])
    id = serializers.IntegerField()


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id', 'name', 'measurement_unit', 'amount'
        )


class RecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    image = Base64ImageField()
    author = ProfileSerializer()
    tags = TagSerializer(many=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'cooking_time', 'image', 'author',
            'tags', 'is_in_shopping_cart', 'is_favorited', 'ingredients'
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return request.user.id and RecipeShop.objects.filter(
            recipe=obj,
            user=request.user
        ).exists()

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.id:
            user = request.user
            return RecipeFavorite.objects.filter(
                recipe=obj, user=user
            ).exists()
        return False

    def get_ingredients(self, obj):
        rec_ingrs = RecipeIngredient.objects.filter(
            recipe=obj
        )
        serializer = RecipeIngredientSerializer(rec_ingrs, many=True)
        return serializer.data


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = TagIdSerializer()
    ingredients = IngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'cooking_time', 'image',
            'tags', 'ingredients'
        )

    def validate(self, data):
        ingredients = data.get('ingredients')
        ingredients_valid = []
        if not ingredients:
            raise ValidationError(
                'Нужны ингредиенты что бы что то приготовить'
            )
        for ingredient in ingredients:
            if ingredient.get('id') in ingredients_valid:
                raise ValidationError(
                    'Зачем тебе два одинаковых ингредиента?'
                )
            if int(ingredient.get('amount')) <= 0:
                raise ValidationError(
                    'Думаешь что ингредиента может быть меньше 0?'
                )
            ingredients_valid.append(ingredient.get('id'))
        return data

    def ingredients_create(self, ingredients, recipe):
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                recipe=recipe,
                amount=int(ingredient['amount']),
                ingredient=ingredient['id']
            ) for ingredient in ingredients]
        )

    def tags_create(self, tags, recipe):
        RecipeTag.objects.bulk_create(
            [RecipeTag(
                recipe=recipe,
                tag=get_object_or_404(Tag, id=tag_id)
            ) for tag_id in tags]
        )

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        author = request.user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data, author=author)
        self.tags_create(tags, recipe)
        self.ingredients_create(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        super().update(instance, validated_data)
        RecipeTag.objects.filter(recipe=instance).delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.tags_create(tags, instance)
        self.ingredients_create(ingredients, instance)
        return instance

    def to_representation(self, obj):
        request = self.context.get('request')
        return RecipeSerializer(obj, context={'request': request}).data


class FavoriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    image = Base64ImageField(read_only=True)
    name = serializers.CharField(read_only=True)
    cooking_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'cooking_time'
        )

    def create(self, validated_data):
        request = self.context.get('request')
        pk = int(self.context.get("pk"))
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        RecipeFavorite.objects.get_or_create(
            recipe=recipe, user=user
        )
        return recipe


class SubscribeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )
        depth = 2

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = self.context.get("recipes_limit")
        recipes_list = Recipe.objects.filter(
            author=obj
        )
        serializer = RecipeSerializer(
            recipes_list, many=True, context={'request': request}
        )
        return serializer.data[:recipes_limit]

    def get_recipes_count(self, obj):
        if self.context.get("pk"):
            pk = int(self.context.get("pk"))
            author = User.objects.get(id=pk)
            return Recipe.objects.filter(
                author=author
            ).count()
        return None

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        if self.context.get("pk"):
            pk = int(self.context.get("pk"))
            author = get_object_or_404(User, id=pk)
            if not Follow.objects.filter(
                author=author, user=user
            ).exists():
                Follow.objects.create(author=author, user=user)
                return author


class RecipeShopSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    image = Base64ImageField(read_only=True)
    name = serializers.CharField(read_only=True)
    cooking_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'cooking_time'
        )

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        pk = int(self.context.get("pk"))
        recipe = get_object_or_404(Recipe, id=pk)
        RecipeShop.objects.create(recipe=recipe, user=user)
        return recipe
