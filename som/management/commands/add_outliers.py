from django.core.management.base import BaseCommand
from django.conf import settings
import os
from som.som_postprocessing import SOM, plot_image, return_cutout
import som.models
import csv
import numpy as np
from django.core.files import File


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
        sorted_proto_idxs = np.argsort(som_obj.data_map, axis=1)
        best_distances = som_obj.data_map[range(som_obj.number_of_images), sorted_proto_idxs[:, 0]]
        # Todo: Check why all images after 60000 throw an error o.O
        sorted_best_distance_idxs = np.argsort(best_distances[:600000])
        print("Generating outliers...")
        with open(som_model.csv_path.path) as csv_file:
            catalog = csv.DictReader(csv_file)
            for outlier_idx in range(1, n_outliers+1):
                print("Outlier {idx} from {total}...".format(idx=outlier_idx, total=n_outliers))
                print(sorted_best_distance_idxs[-outlier_idx])
                outlier_filename = os.path.join('outliers', som_obj.training_dataset_name,
                                                "outlier{0}.png".format(outlier_idx))
                plot_image(return_cutout(som_model.data_path.path, sorted_best_distance_idxs[-outlier_idx]),
                           os.path.join(settings.MEDIA_ROOT, outlier_filename))
                for i, row in enumerate(catalog):
                    if i == sorted_best_distance_idxs[-outlier_idx]:
                        csv_entry = row
                        break

                ra = csv_entry['RA']
                dec = csv_entry['Dec']
                outlier_model = som.models.Outlier(
                    som=som_model,
                    ra=ra,
                    dec=dec,
                    csv_path=som_model.csv_path,
                    csv_row_idx=sorted_best_distance_idxs[-outlier_idx],
                    image=File(os.path.join(settings.MEDIA_ROOT, outlier_filename))
                )
                outlier_model.save()
