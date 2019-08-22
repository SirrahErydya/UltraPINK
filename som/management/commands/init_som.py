from django.core.management.base import BaseCommand
from django.conf import settings
import os
from som.som_postprocessing import SOM, plot_image, return_cutout
import som.models
import csv
import numpy as np
from django.core.files import File


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
        csv_path = os.path.join(settings.DATA_DIR, options['csv_filename']+'.csv')

        print("Parsing SOM binary files (this may take a while)...")
        som_obj = SOM(options['dataset_name'], som_path, mapping_path)
        print("...done")

        # Creating directories
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'prototypes', som_obj.training_dataset_name), exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'cutouts', som_obj.training_dataset_name), exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'outliers', som_obj.training_dataset_name), exist_ok=True)

        print("Generating Database entries for the SOM build for {0}".format(options['dataset_name']))
        print("Creating SOM model...")

        assert options['n_cutouts'] <= som_obj.data_map.shape[0]
        assert options['n_outliers'] <= som_obj.data_map.shape[0]

        # Create SOM model
        som_model = som.models.SOM.objects.create(
            som_path=File(som_path),
            mapping_path=File(mapping_path),
            data_path=File(bindata_path),
            csv_path=File(csv_path),
            n_cutouts=options['n_cutouts'],
            n_outliers=options['n_outliers'],
            training_dataset_name=som_obj.training_dataset_name,
            number_of_images=som_obj.number_of_images,
            number_of_channels=som_obj.number_of_channels,
            som_width=som_obj.som_width,
            som_height=som_obj.som_height,
            som_depth=som_obj.som_depth,
            layout=som_obj.layout,
            som_label=som_obj.som_label,
            rotated_size=som_obj.rotated_size,
            full_size=som_obj.full_size,
            gauss_start=som_obj.gauss_start,
            learning_constraint=som_obj.learning_constraint,
            epochs_per_epoch=som_obj.epochs_per_epoch,
            gauss_decrease=som_obj.gauss_decrease,
            gauss_end=som_obj.gauss_end,
            pbc=som_obj.pbc,
            learning_constraint_decrease=som_obj.learning_constraint_decrease,
            random_seed=som_obj.random_seed,
            init=som_obj.init,
            pix_angular_res=som_obj.pix_angular_res,
            rotated_size_arcsec=som_obj.rotated_size_arcsec,
            full_size_arcsec=som_obj.full_size_arcsec
        )
        print("...done.")

        # Create prototype entries and save the plots
        print("Generating images and database entries for each prototype...")
        with open(csv_path) as csv_file:
            catalog = csv.DictReader(csv_file)
            for x in range(som_obj.som_width):
                for y in range(som_obj.som_height):
                    for z in range(som_obj.som_depth):
                        file_name = os.path.join('prototypes', som_obj.training_dataset_name,
                                                 'prototype{x}{y}{z}.png'.format(x=x, y=y, z=z))
                        proto = som_obj.data_som[x, y, z, :]
                        proto = proto.reshape((som_obj.rotated_size, som_obj.rotated_size))

                        # Plot
                        plot_image(proto, os.path.join(settings.MEDIA_ROOT, file_name))

                        # Save
                        proto_model = som.models.Prototype(
                            proto_id=x*som_obj.som_height+y,
                            som=som_model,
                            x=x,
                            y=y,
                            z=z
                        )
                        proto_model.image.name = file_name
                        proto_model.save()
            print("...done.")

            print("Generating all cutout images and saving them to the database (this is going to take forever...")
            # Save and plot the cutouts
            sorted_proto_idxs = np.argsort(som_obj.data_map, axis=1)
            sorted_best_distance_idxs = np.argsort(som_obj.data_map[:][sorted_proto_idxs[:,0]])
            print(sorted_best_distance_idxs)
            for cutout_idx in range(som_model.n_cutouts):
                print("Cutout {idx} from {total}...".format(idx=cutout_idx, total=som_model.n_cutouts))
                cutout_filename = os.path.join('cutouts', som_obj.training_dataset_name,
                                               "cutout{0}.png".format(cutout_idx))
                plot_image(return_cutout(bindata_path, cutout_idx),
                           os.path.join(settings.MEDIA_ROOT, cutout_filename))
                for i, row in enumerate(catalog):
                    if i == cutout_idx:
                        csv_entry = row
                        break

                ra = csv_entry['RA']
                dec = csv_entry['Dec']
                cutout_model = som.models.SomCutout(
                    som=som_model,
                    ra=ra,
                    dec=dec,
                    csv_path=csv_path,
                    csv_row_idx=cutout_idx,
                    closest_prototype=som.models.Prototype.objects.get(proto_id=sorted_proto_idxs[cutout_idx][0])
                )
                cutout_model.image.name = cutout_filename
                cutout_model.save()
                # Save the distances to each prototype for this cutout
                print("Saving distances to all {no_p} prototypes for cutout {no_c}".format(
                    no_p=som_obj.data_map.shape[1], no_c=cutout_idx))
                for proto_idx in sorted_proto_idxs[cutout_idx]:
                    distance = som_obj.data_map[cutout_idx][proto_idx]
                    prototype = som.models.Prototype.objects.get(proto_id=proto_idx)
                    som.models.Distance.objects.create(
                        distance=distance,
                        prototype=prototype,
                        cutout=cutout_model
                    )
            print("...done.")

            print("Generating outliers...")
            for outlier_idx in sorted_best_distance_idxs[-som_model.n_outliers:]:
                print("Outlier {idx} from {total}...".format(idx=outlier_idx, total=som_model.n_outliers))
                outlier_filename = os.path.join('outliers', som_obj.training_dataset_name,
                                                "outlier{0}.png".format(outlier_idx))
                plot_image(return_cutout(bindata_path, outlier_idx),
                           os.path.join(settings.MEDIA_ROOT, outlier_filename))
                for i, row in enumerate(catalog):
                    if i == cutout_idx:
                        csv_entry = row
                        break

                ra = csv_entry['RA']
                dec = csv_entry['Dec']
                outlier_model = som.models.Outlier(
                    som=som_model,
                    ra=ra,
                    dec=dec,
                    csv_path=csv_path,
                    csv_row_idx=cutout_idx,
                    image=File(os.path.join(settings.MEDIA_ROOT, outlier_filename))
                )
                outlier_model.save()
            print("...done.")
            print("All information from the SOM is loaded to the database now. Thanks for your patience.")
