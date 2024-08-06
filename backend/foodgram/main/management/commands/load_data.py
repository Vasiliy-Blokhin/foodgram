import json
import os
import base64

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand


from main.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeTag,
    Tag,
    User
)


directory = os.path.join(settings.BASE_DIR, 'main/data/')


class Command(BaseCommand):

    def handle(self, *args, **options):
        add_users()
        add_ingredients()
        add_tags()
        add_recipes()


def add_users():
    with open(directory + 'users.json', encoding='utf-8') as json_file:
        for user in json.load(json_file):
            with open(
                directory + 'avatars.json', encoding='utf-8'
            ) as images_file:
                image = json.load(images_file)[0].get(
                    user.get('avatar')
                )
            if user.get('is_superuser', False):
                author = User.objects.create_superuser(
                    email=user.get('email'),
                    username=user.get('username'),
                    first_name=user.get('first_name'),
                    last_name=user.get('last_name'),
                    password=user.get('password'),
                    is_superuser=True,
                    avatar=ContentFile(
                        base64.b64decode(image),
                        name=f"{user.get('avatar')}.jpg"
                    )
                )
            else:
                author = User.objects.create_user(
                    email=user.get('email'),
                    username=user.get('username'),
                    first_name=user.get('first_name'),
                    last_name=user.get('last_name'),
                    password=user.get('password'),
                    avatar=ContentFile(
                        base64.b64decode(image),
                        name=f"{user.get('avatar')}.jpg"
                    )
                )


def add_ingredients():
    with open(
        directory + 'ingredients.json', encoding='utf-8'
    ) as json_file:
        for ingredient in json.load(json_file):
            Ingredient.objects.create(**ingredient)


def add_tags():
    with open(directory + 'tags.json', encoding='utf-8') as json_file:
        for tag in json.load(json_file):
            Tag.objects.create(**tag)


def add_recipes():
    with open(directory + 'recipes.json', encoding='utf-8') as json_file:
        for recipe in json.load(json_file):
            with open(
                directory + 'images.json', encoding='utf-8'
            ) as images_file:
                image = json.load(images_file)[0].get(
                    recipe.get('image')
                )
            finish_recipe = Recipe.objects.create(
                id=recipe.get('id'),
                author=User.objects.get(id=recipe.get('author')),
                name=recipe.get('name'),
                text=recipe.get('text'),
                cooking_time=recipe.get('cooking_time'),
                image=ContentFile(
                    base64.b64decode(image),
                    name=f"{recipe.get('image')}.jpeg"
                )
            )
            RecipeTag.objects.create(
                recipe=finish_recipe,
                tag=Tag.objects.get(id=recipe.get('tag'))
            )
            RecipeIngredient.objects.create(
                recipe=finish_recipe,
                ingredient=Ingredient.objects.get(
                    id=recipe.get('ingredients')
                ),
                amount=recipe.get('amount')
            )
