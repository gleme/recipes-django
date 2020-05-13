from django.test import TestCase
from django.contrib import auth


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
