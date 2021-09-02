from django.db import models
from django.conf import settings
import os


def upload_to_project_folder(instance, file_name):
    return os.path.join("projects", instance.project_name, file_name)


def upload_to_dataset_folder(instance, file_name):
    return os.path.join("projects", instance.project.project_name, instance.dataset_name, file_name)


class Project(models.Model):
    project_name = models.CharField(max_length=200)
    description = models.TextField(max_length=2000)
    thumbnail = models.ImageField(default=None, null=True, upload_to=upload_to_project_folder)


class Catalog(models.Model):
    catalog_name = models.CharField(max_length=200)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    file = models.FileField(upload_to='data')


class Dataset(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    dataset_name = models.CharField(max_length=200)
    description = models.TextField(max_length=2000, default="No description...")
    length = models.IntegerField()
    data_path = models.FileField(upload_to='projects')
    csv_path = models.FileField(upload_to=upload_to_dataset_folder, default=None)
    obj_identifier_key = models.CharField(max_length=200, default="ObjName")