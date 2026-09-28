"""
MongoDB versions of Django's built-in apps.

MongoDB stores ObjectId primary keys, so the admin, auth and contenttypes
apps must create their tables with ObjectIdAutoField instead of numbers.
"""

from django.contrib.admin.apps import AdminConfig
from django.contrib.auth.apps import AuthConfig
from django.contrib.contenttypes.apps import ContentTypesConfig

MONGO_ID = "django_mongodb_backend.fields.ObjectIdAutoField"

class MongoAdminConfig(AdminConfig):
    default_auto_field = MONGO_ID

class MongoAuthConfig(AuthConfig):
    default_auto_field = MONGO_ID


class MongoContentTypesConfig(ContentTypesConfig):
    default_auto_field = MONGO_ID
