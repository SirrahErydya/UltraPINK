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
    protomatch_file = models.FileField(upload_to='projects', null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    heatmap = models.ImageField(default=None, null=True)
    histogram = models.ImageField(default=None, null=True)


class Prototype(models.Model):
    som = models.ForeignKey(SOM, on_delete=models.CASCADE)
    label = models.CharField(max_length=200, default="")
    x = models.IntegerField()
    y = models.IntegerField()
    z = models.IntegerField()
    number_of_fits = models.IntegerField()
    image = models.CharField(max_length=200, default="")

    def to_json(self):
        dictionary = {}
        dictionary['label'] = self.label
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
    ra = models.DecimalField(decimal_places=15, max_digits=20)
    dec = models.DecimalField(decimal_places=15, max_digits=20)
    label = models.CharField(max_length=200, default="")
    image = models.CharField(max_length=200, default="")

    # Map coordinates and image data
    closest_prototype = models.ForeignKey(Prototype, on_delete=models.CASCADE)
    distance = models.DecimalField(decimal_places=15, max_digits=20)

    def to_json(self):
        dictionary = {}
        dictionary['ra'] = self.ra
        dictionary['dec'] = self.ra
        dictionary['label'] = self.label
        dictionary['index'] = self.index
        dictionary['url'] = self.image.url
        dictionary['db_id'] = self.id
        return dictionary






