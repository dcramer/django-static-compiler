from django.core.management import call_command
from django.test import TestCase


class CompileStaticTest(TestCase):
    def test_find_static_files(self):
        call_command('compilestatic')
