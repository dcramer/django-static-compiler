from django.conf import settings


def pytest_configure(config):
    if not settings.configured:
        settings.configure(
            DATABASE_ENGINE='sqlite3',
            DATABASES={
                'default': {
                    'NAME': ':memory:',
                    'ENGINE': 'django.db.backends.sqlite3',
                    'TEST_NAME': ':memory:',
                },
            },
            INSTALLED_APPS=[
                'django.contrib.staticfiles',
                'static_compiler',
            ],
            ROOT_URLCONF='',
            DEBUG=False,
            SITE_ID=1,
            TEMPLATE_DEBUG=True,
        )
