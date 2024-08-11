import random
import string

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from main.constants import (
    MAX_COOK_TIME,
    MAX_EMAIL_LENGTH,
    MAX_LENGTH,
    MIN_COOK_TIME,
    SHORT_URL_LENGTH,
    SHORT_URL_SPLIT,
)


class User(AbstractUser):
    first_name = models.CharField(
        verbose_name='имя пользователя',
        max_length=MAX_LENGTH,
        null=True,
        blank=True
    )
    last_name = models.CharField(
        verbose_name='фамилия пользователя',
        max_length=MAX_LENGTH,
        null=True,
        blank=True
    )
    is_subscribed = models.ManyToManyField(
        'User',
        through='Follow',
        related_name='author',
        verbose_name='подписка',
        blank=True
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/',
        blank=True
    )
    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        unique=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='название тега',
        help_text='Введите название тега',
        unique=True
    )
    slug = models.SlugField(
        verbose_name='идентификатор тега',
        help_text='Введите идентификатор тега',
        unique=True
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='название ингредиента',
        help_text='Введите название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='единица измерения',
        help_text='Введите единицу измерения',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='автор рецепта'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='название рецепта',
        help_text='Введите название рецепта'
    )
    text = models.TextField(
        'описание рецпета',
        help_text='Введите описание рецeпта'
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Теги',
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='время приготовления',
        help_text='Введите время приготовления в минутах',
        default=5,
        validators=[
            MinValueValidator(MIN_COOK_TIME),
            MaxValueValidator(MAX_COOK_TIME)
        ]
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipe/',
        blank=True
    )
    pub_date = models.DateTimeField('дата публикации', auto_now_add=True)
    is_favorited = models.ManyToManyField(
        User,
        through='RecipeFavorite',
        related_name='recipes_favorite',
        verbose_name='лайк рецепт'
    )
    is_in_shopping_cart = models.ManyToManyField(
        User,
        through='RecipeShop',
        related_name='recipe_shop',
        verbose_name='рецепт в корзине'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='рецепт в корзине',
    )

    class Meta:
        ordering = ('pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                name='unique_recipe',
                fields=['name', 'author']
            ),
        ]

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    class Meta:
        ordering = ('-tag',)
        verbose_name = 'связь рецепта и тега'
        verbose_name_plural = 'связь рецепта и тега'
        constraints = [
            models.UniqueConstraint(
                name='unique_tag',
                fields=['recipe', 'tag']
            ),
        ]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='объект подражания'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['author']
        constraints = [
            models.UniqueConstraint(
                name='unique_follow',
                fields=['user', 'author']
            ),
        ]


class RecipeFavorite(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_favorite'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='пользователь'
    )

    class Meta:
        ordering = ('-recipe',)
        verbose_name = 'связь рецепта и пользователя избранное'
        verbose_name_plural = 'связь рецепта и пользователя избранное'
        constraints = [
            models.UniqueConstraint(
                name='unique_favorite',
                fields=['recipe', 'user']
            ),
        ]


class RecipeShop(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_shop'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='пользователь'
    )

    class Meta:
        ordering = ('-recipe',)
        verbose_name = 'связь рецепта и пользователя покупки'
        verbose_name_plural = 'связь рецепта и пользователя покупки'
        constraints = [
            models.UniqueConstraint(
                name='unique_shop',
                fields=['recipe', 'user']
            ),
        ]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='индегриент'
    )
    amount = models.PositiveIntegerField(
        verbose_name='количество ингридиента',
        help_text='Введите количество ингридиента',
    )

    class Meta:
        ordering = ('-recipe',)
        verbose_name = 'связь рецепта и ингредиента'
        verbose_name_plural = 'связь рецепта и ингредиента'
        constraints = [
            models.UniqueConstraint(
                name='unique_ingredient',
                fields=['recipe', 'ingredient']
            ),
        ]


class ShortUrl(models.Model):
    recipe_id = models.PositiveIntegerField()
    short_url = models.SlugField(max_length=MAX_LENGTH)

    @classmethod
    def generate(self):
        return SHORT_URL_SPLIT + ''.join(
            random.choice(string.ascii_letters) for _ in range(
                SHORT_URL_LENGTH
            )
        )

    @classmethod
    def find_slug(self, slug):
        return SHORT_URL_SPLIT + slug
