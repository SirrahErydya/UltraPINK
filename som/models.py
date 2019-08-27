from django.db import models


# Create your models here.
class SOM(models.Model):
    # Important for data management
    som_path = models.FileField(upload_to='bin')
    mapping_path = models.FileField(upload_to='bin')
    data_path = models.FileField(upload_to='bin')
    csv_path = models.FileField(upload_to='data')
    n_cutouts = models.IntegerField()
    n_outliers = models.IntegerField()

    # SOM properties
    training_dataset_name = models.CharField(max_length=200)
    number_of_images = models.IntegerField()
    number_of_channels = models.IntegerField()
    som_width = models.DecimalField(decimal_places=15, max_digits=20)
    som_height = models.DecimalField(decimal_places=15, max_digits=20)
    som_depth = models.DecimalField(decimal_places=15, max_digits=20)
    layout = models.CharField(max_length=200)
    som_label = models.CharField(max_length=200)
    rotated_size = models.DecimalField(decimal_places=15, max_digits=20)
    full_size = models.IntegerField()

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


class Prototype(models.Model):
    proto_id = models.IntegerField(unique=True)
    som = models.ForeignKey(SOM, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='prototypes')
    x = models.IntegerField()
    y = models.IntegerField()
    z = models.IntegerField()


class SomCutout(models.Model):
    # Foreign key
    som = models.ForeignKey(SOM, on_delete=models.CASCADE)

    # Astronomical details
    ra = models.DecimalField(decimal_places=15, max_digits=20)
    dec = models.DecimalField(decimal_places=15, max_digits=20)
    csv_path = models.FilePathField()
    csv_row_idx = models.IntegerField()

    # Map coordinates and image data
    closest_prototype = models.ForeignKey(Prototype, on_delete=models.DO_NOTHING)
    image = models.ImageField(upload_to='cutouts')


class Outlier(models.Model):
    # Foreign key
    som = models.ForeignKey(SOM, on_delete=models.CASCADE)

    # Astronomical details
    ra = models.DecimalField(decimal_places=15, max_digits=20)
    dec = models.DecimalField(decimal_places=15, max_digits=20)
    csv_path = models.FilePathField()
    csv_row_idx = models.IntegerField()

    # Image data
    image = models.ImageField(upload_to='outliers')


class Distance(models.Model):
    prototype = models.ForeignKey(Prototype, on_delete=models.CASCADE)
    cutout = models.ForeignKey(SomCutout, on_delete=models.CASCADE)
    distance = models.DecimalField(decimal_places=15, max_digits=20)

