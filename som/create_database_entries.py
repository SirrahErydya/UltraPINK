"""
This is a collection of functions to automatically create database entries with SOM components
:author: Fenja Kollasch
"""
import som.models
import os
import numpy as np
from django.conf import settings
from som.som_postprocessing import plot_image, return_cutout


def create_som_model(project, som_path, mapping_path, bindata_path, csv_path, som_obj, n_cutouts=1000, n_outliers=100):
    """
    Create a database model for a complete SOM capsuling the data
    :param project: The project that this SOM belongs to
    :param som_path: Path to the SOM binary file
    :param mapping_path: Path to the mapping binary file
    :param bindata_path: Path to the image binary file
    :param csv_path: Path to the CSV file containing the celestial positions
    :param som_obj: A Python object that contains all relevant SOM information
    :param n_cutouts: The number of cutouts that initially should be saved to the database
    :param n_outliers: The number of outlier images that initially should be saved to the database
    :return: A Django Database model of the given SOM
    """
    print("Generating Database entries for the SOM build for {0}".format(som_obj))
    print("Creating SOM model...")

    assert n_cutouts <= som_obj.data_map.shape[0]
    assert n_outliers <= som_obj.data_map.shape[0]

    # Create SOM model
    som_model = som.models.SOM.objects.create(
        project=project,
        som_path=som_path,
        mapping_path=mapping_path,
        data_path=bindata_path,
        csv_path=csv_path,
        n_cutouts=n_cutouts,
        n_outliers=n_outliers,
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
    return som_model


def create_prototype_models(som_model, prototypes):
    """
    Generate images and database entries for each prototype in the map
    :param som_model: The SOM database model that belongs to these prototypes
    :param prototypes: All prototypes as numpy arrays
    """
    for x in range(som_model.som_width):
        for y in range(som_model.som_height):
            for z in range(som_model.som_depth):
                file_name = os.path.join('prototypes', som_model.training_dataset_name,
                                         'prototype{x}{y}{z}.png'.format(x=x, y=y, z=z))
                proto = prototypes[x, y, z, :]
                proto = proto.reshape((som_model.rotated_size, som_model.rotated_size))

                # Plot
                plot_image(proto, os.path.join(settings.MEDIA_ROOT, file_name))

                # Save
                proto_model = som.models.Prototype(
                    proto_id=x * som_model.som_height + y,
                    som=som_model,
                    x=x,
                    y=y,
                    z=z
                )
                proto_model.image.name = file_name
                proto_model.save()
    print("...done.")


def create_cutout_models(som_model, mapping, catalog, n_cutouts):
    """
    Generate images and database entries for the map-specific dataset
    Furthermore, save the distance to all prototypes to the database
    :param som_model: The SOM database model that belongs to these cutouts
    :param mapping: An array containing the distances of the cutouts to each prototype
    :param catalog: A csv file containing the sky position of the image objects
    :param n_cutouts: The number of cutouts that will be saved
    :return:
    """
    print("Generating all cutout images and saving them to the database (this is going to take forever...")
    # Save and plot the cutouts
    sorted_proto_idxs = np.argsort(mapping, axis=1)
    sorted_best_distance_idxs = np.argsort(mapping[:][sorted_proto_idxs[:, 0]])
    print(sorted_best_distance_idxs)
    for cutout_idx in range(n_cutouts):
        print("Cutout {idx} from {total}...".format(idx=cutout_idx, total=n_cutouts))
        cutout_filename = os.path.join('cutouts', som_model.training_dataset_name,
                                       "cutout{0}.png".format(cutout_idx))
        plot_image(return_cutout(som_model.data_path.path, cutout_idx),
                   os.path.join(settings.MEDIA_ROOT, cutout_filename))
        ra, dec = get_sky_coords(catalog, cutout_idx)
        cutout_model = som.models.SomCutout(
            som=som_model,
            ra=ra,
            dec=dec,
            csv_path=som_model.csv_path,
            csv_row_idx=cutout_idx,
            closest_prototype=som.models.Prototype.objects.get(proto_id=sorted_proto_idxs[cutout_idx][0])
        )
        cutout_model.image.name = cutout_filename
        cutout_model.save()

        # Save the distances to each prototype for this cutout
        print("Saving distances to all {no_p} prototypes for cutout {no_c}".format(
            no_p=mapping.shape[1], no_c=cutout_idx))
        for proto_idx in sorted_proto_idxs[cutout_idx]:
            distance = mapping[cutout_idx][proto_idx]
            prototype = som.models.Prototype.objects.get(proto_id=proto_idx)
            som.models.Distance.objects.create(
                distance=distance,
                prototype=prototype,
                cutout=cutout_model
            )
    print("...done.")


def create_outliers(som_model, mapping, catalog, n_outliers):
    """
    Generate images and database entries for the outliers of the map
    :param som_model: The SOM database model that belongs to these outliers
    :param mapping: An array containing the distances of the cutouts to each prototype
    :param catalog: A csv file containing the sky position of the image objects
    :param n_outliers: The number of outliers that should be saved
    :return:
    """
    sorted_proto_idxs = np.argsort(mapping, axis=1)
    best_distances = mapping[range(som_model.number_of_images), sorted_proto_idxs[:, 0]]
    # Todo: Check why all images after 60000 throw an error o.O
    sorted_best_distance_idxs = np.argsort(best_distances[:600000])
    print("Generating outliers...")
    for outlier_idx in range(n_outliers):
        print("Outlier {idx} from {total}...".format(idx=outlier_idx, total=n_outliers))
        outlier_filename = os.path.join('outliers', som_model.training_dataset_name,
                                        "outlier{0}.png".format(outlier_idx))
        plot_image(return_cutout(som_model.data_path.path, sorted_best_distance_idxs[-outlier_idx]),
                   os.path.join(settings.MEDIA_ROOT, outlier_filename))
        ra, dec = get_sky_coords(catalog, sorted_best_distance_idxs[-outlier_idx])
        outlier_model = som.models.Outlier(
            som=som_model,
            ra=ra,
            dec=dec,
            csv_path=som_model.csv_path,
            csv_row_idx=sorted_best_distance_idxs[-outlier_idx]
        )
        outlier_model.image.name = outlier_filename
        outlier_model.save()


def get_sky_coords(catalog, idx):
    """
    Get the celestial position of an object
    :param catalog: A csv file containing the sky positions
    :param idx: The position of the object of interest in the catalog
    :return: Right ascension and declination of the object at position idx
    """
    csv_entry = None
    for i, row in enumerate(catalog):
        if i == idx:
            csv_entry = row
            break

    if csv_entry is not None:
        return csv_entry['RA'], csv_entry['Dec']
    return 0.0, 0.0
