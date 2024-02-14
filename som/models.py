from django.db import models
from pinkproject.models import Dataset
from django.conf import settings
from astropy.io import votable as vot
from astropy.io.votable import ucd as vucd
import os


def upload_to_som_folder(instance, file_name=""):
    return os.path.join("projects", instance.dataset.project.project_name, instance.dataset.dataset_name,
                        "soms", instance.som_name, file_name)


# Create your models here.
class SOM(models.Model):
    # SOM properties
    som_name = models.CharField(max_length=200)
    som_width = models.IntegerField()
    som_height = models.IntegerField()
    som_depth = models.IntegerField()
    layout = models.CharField(max_length=200)
    number_of_neurons = models.IntegerField()
    mapping_generated = models.BooleanField(default=False)

    # Important for data management
    som_file = models.FileField(upload_to='projects')
    mapping_file = models.FileField(upload_to='projects', null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    heatmap = models.ImageField(default=None, null=True)
    histogram = models.ImageField(default=None, null=True)
    proto_grid = models.ImageField(default=None, null=True)


class Label(models.Model):
    som = models.ForeignKey(SOM, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True)
    color_r = models.IntegerField(default=255)
    color_g = models.IntegerField(default=255)
    color_b = models.IntegerField(default=255)

    def to_json(self):
        dictionary = {}
        dictionary['name'] = self.name
        dictionary['r'] = self.color_r
        dictionary['g'] = self.color_g
        dictionary['b'] = self.color_b
        return dictionary


class Prototype(models.Model):
    som = models.ForeignKey(SOM, on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.SET_NULL, null=True)
    index = models.IntegerField()
    x = models.IntegerField()
    y = models.IntegerField()
    z = models.IntegerField()
    number_of_fits = models.IntegerField()
    image = models.CharField(max_length=200, default="")

    def to_json(self):
        dictionary = {}
        if self.label:
            dictionary['label'] = self.label.to_json()
        else:
            dictionary['label'] = ""
        dictionary['x'] = self.x
        dictionary['y'] = self.y
        dictionary['z'] = self.z
        dictionary['number_fits'] = self.number_of_fits
        return dictionary


class DataPoint(models.Model):
    # Foreign key
    som = models.ForeignKey(SOM, on_delete=models.CASCADE)
    index = models.IntegerField()
    label = models.ForeignKey(Label, on_delete=models.SET_NULL, null=True)
    image = models.CharField(max_length=200, default="")
    closest_proto = models.ForeignKey(Prototype, on_delete=models.SET_NULL, null=True)

    def to_json(self, proto_dist=None):
        dictionary = {}
        if self.label:
            dictionary['label'] = self.label.to_json()
        else:
            dictionary['label'] = ""
        dictionary['index'] = self.index
        dictionary['url'] = self.image
        dictionary['db_id'] = self.id
        dictionary['closest_proto'] = self.closest_proto.to_json()
        if proto_dist:
            dictionary['distance'] = proto_dist
        return dictionary

    def catalog_data(self):
        if self.som.dataset.catalog_path is None:
            print("No catalog belongs to this dataset.")
            return None
        catalog = vot.parse_single_table(self.som.dataset.catalog_path)
        headers = [ field.name for field in catalog.fields ]
        data = catalog.array[self.index]
        return dict(zip(headers, data))

    def value_by_ucd(self, ucd):
        if self.som.dataset.catalog_path is None:
            print("No catalog belongs to this dataset.")
            return None
        catalog = vot.parse_single_table(self.som.dataset.catalog_path)
        search_ucds = set(vucd.parse_ucd(ucd))
        for field in catalog.fields:
            field_ucds = set(vucd.parse_ucd(field.ucd))
            if search_ucds & field_ucds:
                return catalog.to_table(use_names_over_ids=True)[field.name][self.index]
        print("No Field with UCD {} found".format(ucd))
        return None

    class Meta:
        unique_together = ('som', 'index')







