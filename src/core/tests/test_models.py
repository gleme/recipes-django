from unittest import mock
from django.test import TestCase
from django.contrib import auth

from core import models


def sample_user(email='test@example.com', password='pwd123'):
    """Creates a sample user"""
    return auth.get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        email = 'test@example.com'
        password = 'pass123'
        new_user = auth.get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(new_user.email, email)
        self.assertTrue(new_user.check_password(password))

    def test_new_user_email_is_normalized(self):
        """Test the email for a new user is normalized"""
        email = "test@EXAMPLE.COM"
        user = auth.get_user_model().objects.create_user(email, 'pass123')
        self.assertEqual(user.email, "test@example.com")

    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            auth.get_user_model().objects.create_user(None, 'pass123')

    def test_create_new_superuser(self):
        """Test creating a new superuser"""
        user = auth.get_user_model().objects.create_superuser(
            'test@example.com',
            'pass123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Test the tag string representation"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Vegan'
        )

        self.assertEqual(str(tag), tag.name)

    def test_ingredients_str(self):
        """Test the ingredient string representation"""
        ingredient = models.Ingredient.objects.create(
            user=sample_user(),
            name='Cucumber'
        )
        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        """Tests the recipe string representation"""
        recipe = models.Recipe.objects.create(
            user=sample_user(),
            title='Steak and mushroom sauce',
            time_minutes=5,
            price=5.00
        )

        self.assertEqual(str(recipe), recipe.title)

    @mock.patch('uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test that image is saved in the correct location"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'myimage.jpg')
        exp_path = f'uploads/recipes/{uuid}.jpg'
        self.assertEqual(file_path, exp_path)
