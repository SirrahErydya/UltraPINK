from django.core.management.base import BaseCommand
from django.conf import settings
import os
from som.som_postprocessing import SOM
from pinkproject.models import Project
import csv
import UltraPINK.create_database_entries as dbe


class Command(BaseCommand):
    help = 'Initialize the database with a trained som file'

    def add_arguments(self, parser):
        parser.add_argument("dataset_name", type=str)
        parser.add_argument('som_filename', type=str)
        parser.add_argument('mapping_filename', type=str)
        parser.add_argument('data_filename', type=str)
        parser.add_argument('csv_filename', type=str)
        parser.add_argument('n_cutouts', type=int, default=1000)
        parser.add_argument('n_outliers', type=int, default=100)

    def handle(self, *args, **options):
        som_path = os.path.join(settings.BIN_DIR, options['som_filename']+'.bin')
        mapping_path = os.path.join(settings.BIN_DIR, options['mapping_filename']+'.bin')
        bindata_path = os.path.join(settings.BIN_DIR, options['data_filename']+'.bin')
        som_obj_path = os.path.join(settings.BIN_DIR, 'som_'+options['dataset_name']+'.pkl')
        csv_path = os.path.join(settings.DATA_DIR, options['csv_filename']+'.csv')

        print("Parsing SOM binary files (this may take a while)...")
        som_obj = SOM(options['dataset_name'], som_path, mapping_path, som_obj_path)
        som_obj.save()
        print("...done")

        # Creating directories
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'prototypes', som_obj.training_dataset_name), exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'data', som_obj.training_dataset_name), exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'outliers', som_obj.training_dataset_name), exist_ok=True)

        project = Project(project_name="test", description='test')
        project.save()
        som_model = dbe.create_som_model(project, som_path, mapping_path, bindata_path, csv_path, som_obj)

        # Create prototype entries and save the plots
        dbe.create_prototype_models(som_model, som_obj.data_som)

        # Create cutouts and distances
        with open(som_model.csv_path.path) as csv_file:
            catalog = csv.DictReader(csv_file)
            dbe.create_cutout_models(som_model, som_obj.data_map, catalog, som_model.n_cutouts)

            # Create outliers
            dbe.create_outliers(som_model, som_obj.data_map, catalog, som_model.n_outliers)
        print("All information from the SOM is loaded to the database now. Thanks for your patience.")
