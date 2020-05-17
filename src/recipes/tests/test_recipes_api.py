import tempfile
import os

from PIL import Image

from django.contrib import auth
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipes.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipes:recipe-list')


def image_upload_url(recipe_id: int):
    """Return url for recipe image upload"""
    return reverse('recipes:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id: int):
    """Return recipe detail URL"""
    return reverse('recipes:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Dessert') -> Tag:
    """Creates and returns a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Salt') -> Ingredient:
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **kwargs) -> Recipe:
    """Creates a sample recipe"""
    defaults = {
        'title': 'Cheese burger',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(kwargs)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_authentication_required(self):
        """Test that authnetication is required"""
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Tests unauthenticated recipe API access"""

    def setUp(self) -> None:
        self.user = auth.get_user_model().objects.create_user(
            'test@example.com',
            'pwd123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Tests retrieving recipes only from the user"""
        another_user = auth.get_user_model().objects.create_user(
            'another@example.com',
            'pwd123',
        )
        sample_recipe(user=another_user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Tests viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        serializer = RecipeDetailSerializer(recipe)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            'title': 'Cheesecake',
            'time_minutes': 30,
            'price': 5.00
        }
        res = self.client.post(RECIPES_URL, payload)
        recipe = Recipe.objects.get(id=res.data['id'])
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating recipe with tag"""
        vegan_tag = sample_tag(user=self.user, name='Vegan')
        dessert_tag = sample_tag(user=self.user)
        payload = {
            'title': 'Cheesecake',
            'tags': [vegan_tag.id, dessert_tag.id],
            'time_minutes': 60,
            'price': 20.00
        }
        res = self.client.post(RECIPES_URL, payload)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(tags.count(), 2)
        self.assertIn(vegan_tag, tags)
        self.assertIn(dessert_tag, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating recipe with ingredients"""
        salt = sample_ingredient(user=self.user)
        pepper = sample_ingredient(user=self.user, name='Pepper')
        payload = {
            'title': 'Hot Mix',
            'ingredients': [salt.id, pepper.id],
            'time_minutes': 5,
            'price': 4.00,
        }
        res = self.client.post(RECIPES_URL, payload)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(salt, ingredients)
        self.assertIn(pepper, ingredients)

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='Curry')
        payload = {'title': 'Carrot Cake', 'tags': [new_tag.id]}
        res = self.client.patch(detail_url(recipe.id), payload)
        recipe.refresh_from_db()
        tags = recipe.tags.all()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test updating a recipe with put"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {
            'title': 'Spaghetti Carbonara',
            'time_minutes': 25,
            'price': 5.0
        }
        res = self.client.put(detail_url(recipe.id), payload)
        recipe.refresh_from_db()
        tags = recipe.tags.all()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        self.assertEqual(len(tags), 0)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class RecipeImageUploadTests(TestCase):
    """Recipe image upload feature tests"""

    def setUp(self) -> None:
        self.user = auth.get_user_model().objects.create_user(
            'test@example.com',
            'pwd123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
            img = Image.new('RGB', (10, 10))
            img.save(temp_file, format='JPEG')
            temp_file.seek(0)
            payload = {'image': temp_file}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipes_by_tags(self):
        """Test returning recipes with specific tags"""
        curry = sample_recipe(user=self.user, title='Curry')
        vegan = sample_tag(user=self.user, name='Vegan')
        curry.tags.add(vegan)
        barbecue = sample_recipe(user=self.user, title='American Barbecue')
        meat_lovers = sample_tag(user=self.user, name='Meat Lovers')
        barbecue.tags.add(meat_lovers)
        carrot_cake = sample_recipe(user=self.user, title='Carrot Cake')
        homemade = sample_tag(user=self.user, name='Homemade')
        carrot_cake.tags.add(homemade)
        payload = {'tags': f'{vegan.id},{meat_lovers.id}'}
        curry_data = RecipeSerializer(curry).data
        barbecue_data = RecipeSerializer(barbecue).data
        carrot_cake_data = RecipeSerializer(carrot_cake).data

        res = self.client.get(RECIPES_URL, payload)

        self.assertIn(curry_data, res.data)
        self.assertIn(barbecue_data, res.data)
        self.assertNotIn(carrot_cake_data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """Test retuning recipes with specific ingredients"""
        curry = sample_recipe(user=self.user, title='Curry')
        barbecue = sample_recipe(user=self.user, title='American Barbecue')
        carrot_cake = sample_recipe(user=self.user, title='Carrot Cake')
        potatoes = sample_ingredient(user=self.user, name='Potatoes')
        carrot = sample_ingredient(user=self.user, name='Carrot')
        salt = sample_ingredient(user=self.user)
        curry.ingredients.add(potatoes)
        curry.ingredients.add(carrot)
        curry.ingredients.add(salt)
        barbecue.ingredients.add(salt)
        carrot_cake.ingredients.add(carrot)

        payload = {'ingredients': f'{potatoes.id},{salt.id}'}
        curry_data = RecipeSerializer(curry).data
        barbecue_data = RecipeSerializer(barbecue).data
        carrot_cake_data = RecipeSerializer(carrot_cake).data

        res = self.client.get(RECIPES_URL, payload)

        self.assertIn(curry_data, res.data)
        self.assertIn(barbecue_data, res.data)
        self.assertNotIn(carrot_cake_data, res.data)
