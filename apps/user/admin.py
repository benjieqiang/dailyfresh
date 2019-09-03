from django.contrib import admin

# Register your models here.
from apps.user import models

admin.site.register(models.User)