from django.db import models
from pinkproject.models import Project
import os
import pickle


# Create your models here.
class SOM(models.Model):
    # SOM properties
    training_dataset_name = models.CharField(max_length=200)
    number_of_images = models.IntegerField()
    number_of_channels = models.IntegerField()
    som_width = models.IntegerField()
    som_height = models.IntegerField()
    som_depth = models.IntegerField()
    layout = models.IntegerField()
    som_label = models.CharField(max_length=200)
    rotated_size = models.DecimalField(decimal_places=15, max_digits=20)
    full_size = models.IntegerField()

    # Important for data management
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    som_obj = models.FileField(upload_to=os.path.join('bin', str(training_dataset_name)))
    som_path = models.FileField(upload_to=os.path.join('bin', str(training_dataset_name)))
    mapping_path = models.FileField(upload_to=os.path.join('bin', str(training_dataset_name)))
    data_path = models.FileField(upload_to=os.path.join('bin', str(training_dataset_name)))
    csv_path = models.FileField(upload_to=os.path.join('data', str(training_dataset_name)))
    heatmap = models.ImageField(upload_to=os.path.join('prototypes', str(training_dataset_name)))
    histogram = models.ImageField(upload_to=os.path.join('data', str(training_dataset_name)))
    current = models.BooleanField(default=False)

    # Training parameters
    gauss_start = models.DecimalField(decimal_places=15, max_digits=20)
    learning_constraint = models.DecimalField(decimal_places=15, max_digits=20)
    epochs_per_epoch = models.DecimalField(decimal_places=15, max_digits=20)
    gauss_decrease = models.DecimalField(decimal_places=15, max_digits=20)
    gauss_end = models.DecimalField(decimal_places=15, max_digits=20)
    pbc = models.CharField(max_length=200)
    learning_constraint_decrease = models.DecimalField(decimal_places=15, max_digits=20)
    random_seed = models.DecimalField(decimal_places=15, max_digits=20)
    init = models.CharField(max_length=200)
    pix_angular_res = models.DecimalField(decimal_places=15, max_digits=20)
    rotated_size_arcsec = models.DecimalField(decimal_places=15, max_digits=20)
    full_size_arcsec = models.DecimalField(decimal_places=15, max_digits=20)

    def load_som_obj(self):
        with open(self.som_obj.path, 'rb') as file:
            return pickle.load(file)


class Prototype(models.Model):
    proto_id = models.IntegerField(unique=True)
    som = models.ForeignKey(SOM, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='prototypes')
    histogram = models.ImageField(upload_to='prototypes')
    label = models.CharField(max_length=200, default="")
    x = models.IntegerField()
    y = models.IntegerField()
    z = models.IntegerField()
    number_of_fits = models.IntegerField()

    def to_json(self):
        dictionary = {}
        dictionary['proto_id'] = self.proto_id
        dictionary['label'] = self.label
        dictionary['x'] = self.x
        dictionary['y'] = self.y
        dictionary['z'] = self.z
        dictionary['url'] = self.image.url
        dictionary['number_fits'] = self.number_of_fits
        return dictionary


class SomCutout(models.Model):
    # Foreign key
    som = models.ForeignKey(SOM, on_delete=models.CASCADE)

    # Astronomical details
    ra = models.DecimalField(decimal_places=15, max_digits=20)
    dec = models.DecimalField(decimal_places=15, max_digits=20)
    csv_path = models.FilePathField()
    csv_row_idx = models.IntegerField()
    label = models.CharField(max_length=200, default="")

    # Map coordinates and image data
    closest_prototype = models.ForeignKey(Prototype, on_delete=models.DO_NOTHING)
    distance = models.DecimalField(decimal_places=15, max_digits=20)
    image = models.ImageField(upload_to='data')

    def to_json(self):
        dictionary = {}
        dictionary['ra'] = self.ra
        dictionary['dec'] = self.ra
        dictionary['label'] = self.label
        dictionary['url'] = self.image.url
        dictionary['db_id'] = self.id
        return dictionary


class Outlier(models.Model):
    # Foreign key
    som = models.ForeignKey(SOM, on_delete=models.CASCADE)

    # Astronomical details
    ra = models.DecimalField(decimal_places=15, max_digits=20)
    dec = models.DecimalField(decimal_places=15, max_digits=20)
    csv_path = models.FilePathField()
    csv_row_idx = models.IntegerField()
    label = models.CharField(max_length=200, default="")

    distance = models.DecimalField(decimal_places=15, max_digits=20)

    # Image data
    image = models.ImageField(upload_to='outliers')

    def to_json(self):
        dictionary = {}
        dictionary['ra'] = self.ra
        dictionary['dec'] = self.ra
        dictionary['label'] = self.label
        dictionary['url'] = self.image.url
        dictionary['db_id'] = self.id
        return dictionary



