from django.db import models
from pinkproject.models import Dataset
from django.conf import settings


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


class Label(models.Model):
    som = models.ForeignKey(SOM, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True)
    color_r = models.IntegerField()
    color_g = models.IntegerField()
    color_b = models.IntegerField()

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
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    index = models.IntegerField()

    # Astronomical details
    ra = models.DecimalField(decimal_places=15, max_digits=20, null=True)
    dec = models.DecimalField(decimal_places=15, max_digits=20, null=True)
    label = models.ForeignKey(Label, on_delete=models.SET_NULL, null=True)
    image = models.CharField(max_length=200, default="")

    def to_json(self, proto_dist=None):
        dictionary = {}
        if self.ra and self.dec:
            dictionary['ra'] = self.ra
            dictionary['dec'] = self.ra
        if self.label:
            dictionary['label'] = self.label.to_json()
        else:
            dictionary['label'] = ""
        dictionary['index'] = self.index
        dictionary['url'] = self.image
        dictionary['db_id'] = self.id
        if proto_dist:
            dictionary['distance'] = proto_dist
        return dictionary

    class Meta:
        unique_together = ('dataset', 'index')







