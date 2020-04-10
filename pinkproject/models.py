from django.db import models
from django.conf import settings


class Project(models.Model):
    project_name = models.CharField(max_length=200)
    description = models.TextField(max_length=2000)


class Catalog(models.Model):
    catalog_name = models.CharField(max_length=200)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    file = models.FileField(upload_to='data')


class Dataset(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    dataset_name = models.CharField(max_length=200)
    length = models.IntegerField()
    data_path = models.FilePathField(path=settings.PROJECT_DIR, recursive=True)
    csv_path = models.FileField(upload_to='projects')

