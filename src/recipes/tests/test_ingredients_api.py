from django.contrib import auth
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipes.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipes:ingredient-list')


class PublicIngredientsAPITests(TestCase):
    """Tests the publicly available ingredients API"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access the endpoint"""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):
    """Tests the private ingredients API"""

    def setUp(self) -> None:
        self.user = auth.get_user_model().objects.create_user(
            'test@example.com',
            'pwd123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients_list(self):
        """Tests retrieving a list of ingredients"""
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Salt')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Tests that ingredients for the authenticated user are returned"""
        another_user = auth.get_user_model().objects.create_user(
            'another@example.com',
            'pwd123'
        )

        Ingredient.objects.create(name='Pepper', user=another_user)
        ingredient = Ingredient.objects.create(name='Salt', user=self.user)

        res = self.client.get(INGREDIENTS_URL)

        ingredients = IngredientSerializer(res.data, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(ingredients.data), 1)
        self.assertEqual(ingredients.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """Tests creating a new ingredient"""
        payload = {'name': 'Cabbage'}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertTrue(exists)

    def test_create_invalid_ingredient(self):
        """Tests creating an invalid ingredient fails"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
