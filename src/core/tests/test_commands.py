from unittest import mock
from django.core import management
from django.db.utils import OperationalError
from django.test import TestCase


class CommandTests(TestCase):

    def test_wait_for_db_ready(self):
        """Test waiting for db when db is available"""
        with mock.patch('django.db.utils.ConnectionHandler.__getitem__') as gi:
            gi.return_value = True
            management.call_command('wait_for_db')
            self.assertEqual(gi.call_count, 1)

    @mock.patch('time.sleep', return_value=True)
    def test_wait_for_db(self, sleep):
        """Test waiting for database"""
        with mock.patch('django.db.utils.ConnectionHandler.__getitem__') as gi:
            gi.side_effect = [OperationalError] * 5 + [True]
            management.call_command('wait_for_db')
            self.assertEqual(gi.call_count, 6)
