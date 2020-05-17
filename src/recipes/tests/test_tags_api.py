from django.contrib import auth
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipes.serializers import TagSerializer

TAGS_URL = reverse('recipes:tag-list')


class PublicTagsApiTests(TestCase):
    """Test the publicly available tags API"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """Tests that login is required for retrieving tags"""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):

    def setUp(self) -> None:
        self.user = auth.get_user_model().objects.create_user(
            'test@example.com',
            'pass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Tests retrieving tags"""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Tests that tags returned are for the authenticated user"""
        another_user = auth.get_user_model().objects.create_user(
            'another@example.com',
            'pass123'
        )
        Tag.objects.create(user=another_user, name='Fruity')
        tag = Tag.objects.create(user=self.user, name='Comfort Food')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        """Tests creating a new tag"""
        payload = {'name': 'test'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        """Tests creating a new tag with invalid payload"""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        """Test filtering tags by those assigned to recipes"""
        breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        lunch = Tag.objects.create(user=self.user, name='Lunch')
        gods_breakfast = Recipe.objects.create(
            title='Bacon and Eggs',
            time_minutes=10,
            price=30.00,
            user=self.user,
        )
        gods_breakfast.tags.add(breakfast)
        breakfast_data = TagSerializer(breakfast).data
        lunch_data = TagSerializer(lunch).data

        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertIn(breakfast_data, res.data)
        self.assertNotIn(lunch_data, res.data)

    def test_retrieve_tags_assigned_distinct(self):
        """Test filtering tags by assigned returns distinct and unique items"""
        breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Lunch')
        gods_breakfast = Recipe.objects.create(
            title='Bacon and Eggs',
            time_minutes=10,
            price=30.00,
            user=self.user,
        )
        pbj = Recipe.objects.create(
            title='Peanut butter and jelly sandwich',
            time_minutes=5,
            price=2.00,
            user=self.user
        )
        gods_breakfast.tags.add(breakfast)
        pbj.tags.add(breakfast)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
