from django.contrib import admin
from pinkproject.models import Project, Catalog, Dataset


# Register your models here.
admin.site.register(Project)
admin.site.register(Catalog)
admin.site.register(Dataset)
