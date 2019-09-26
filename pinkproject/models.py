from django.db import models


class Project(models.Model):
    project_name = models.CharField(max_length=200)
    description = models.TextField(max_length=2000)


class Catalog(models.Model):
    catalog_name = models.CharField(max_length=200)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    file = models.FileField(upload_to='data')
