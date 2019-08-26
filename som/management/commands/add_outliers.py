from django.core.management.base import BaseCommand
from django.conf import settings
import os
from som.som_postprocessing import SOM, plot_image, return_cutout
import som.models
import csv
from som.create_database_entries import create_outliers


class Command(BaseCommand):
    help = 'Add outliers to database'

    def add_arguments(self, parser):
        parser.add_argument('n_outliers', type=int, default=100)
        parser.add_argument('som_id', type=int, default=0)

    def handle(self, *args, **options):
        n_outliers = options['n_outliers']
        som_id = options['som_id']
        som_model = som.models.SOM.objects.get(id=som_id)
        print("Parsing SOM binary files (this may take a while)...")
        som_obj = SOM(som_model.training_dataset_name, som_model.som_path.path, som_model.mapping_path.path)
        with open(som_model.csv_path.path) as csv_file:
            catalog = csv.DictReader(csv_file)
            create_outliers(som_model, som_obj.data_map, catalog, n_outliers)
