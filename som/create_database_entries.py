"""
This is a collection of functions to automatically create database entries with SOM components
:author: Fenja Kollasch
"""
import som.models
import os
import numpy as np
from django.conf import settings
from som.som_postprocessing import plot_image, return_cutout
import matplotlib.pyplot as plt
from matplotlib import image as mpimg
from matplotlib import gridspec as gridspec
import csv


def create_som_model(project, som_path, mapping_path, bindata_path, csv_path, som_obj):
    """
    Create a database model for a complete SOM capsuling the data
    :param project: The project that this SOM belongs to
    :param som_path: Path to the SOM binary file
    :param mapping_path: Path to the mapping binary file
    :param bindata_path: Path to the image binary file
    :param csv_path: Path to the CSV file containing the celestial positions
    :param som_obj: A Python object that contains all relevant SOM information
    :return: A Django Database model of the given SOM
    """
    print("Generating Database entries for the SOM build for {0}".format(som_obj))
    print("Creating SOM model...")

    # Create SOM model
    som_model = som.models.SOM.objects.create(
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
        project=project,
        som_obj=som_obj.som_obj_path,
        som_path=som_path,
        mapping_path=mapping_path,
        data_path=bindata_path,
        csv_path=csv_path,
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
    som_obj = som_model.load_som_obj()
    best_protos = som_obj.sorted_proto_idxs[:,0]
    figure = plt.figure(figsize=(som_model.som_width, som_model.som_height), frameon=False)
    grid = gridspec.GridSpec(som_model.som_width, som_model.som_height)
    grid.update(wspace=0.05, hspace=0.05)

    heatmap = np.ndarray((som_model.som_width, som_model.som_height))
    i = 0
    for y in range(som_model.som_height):
        for x in range(som_model.som_width):
            for z in range(som_model.som_depth):
                file_name = os.path.join('prototypes', som_model.training_dataset_name,
                                         'prototype{x}{y}{z}.png'.format(x=x, y=y, z=z))
                proto = prototypes[x, y, z, :]
                proto = proto.reshape((som_model.rotated_size, som_model.rotated_size))

                # Plot
                plot_image(proto, os.path.join(settings.MEDIA_ROOT, file_name))

                proto_id = x * som_model.som_height + y
                number_of_fits = np.extract(best_protos == proto_id, best_protos).shape[0]

                # Save
                proto_model = som.models.Prototype(
                    proto_id=proto_id,
                    som=som_model,
                    x=x,
                    y=y,
                    z=z,
                    number_of_fits=number_of_fits
                )
                proto_model.image.name = file_name
                proto_model.save()

                # Generate joined image
                axis = plt.subplot(grid[i])
                axis.set_axis_off()
                axis.imshow(mpimg.imread(proto_model.image.path))
                heatmap[y][x] = number_of_fits
                i += 1

    plt.subplots_adjust(wspace=0, hspace=0)
    proto_map_file = os.path.join('prototypes', som_model.training_dataset_name,  'protos.png')
    heatmap_file = os.path.join('prototypes', som_model.training_dataset_name, 'heatmap.png')
    figure.savefig(os.path.join(settings.MEDIA_ROOT, proto_map_file))
    save_heatmap(heatmap, heatmap_file)
    som_model.proto_map.name = proto_map_file
    som_model.heatmap.name = heatmap_file
    som_model.save()
    print("...done.")


def save_heatmap(heatmap, filename):
    figure = plt.figure(frameon=False)
    axis = plt.Axes(figure, [0., 0., 1., 1.])
    axis.set_axis_off()
    figure.add_axes(axis)
    for y in range(heatmap.shape[0]):
        for x in range(heatmap.shape[1]):
            axis.text(x, y, heatmap[y][x], ha="center", va="center", color="w")
    axis.imshow(heatmap)
    figure.savefig(os.path.join(settings.MEDIA_ROOT, filename))


def create_cutouts_for_prototype(prototype, n_cutouts):
    som_model = som.models.SOM.objects.get(id=prototype.som_id)
    som_obj = som_model.load_som_obj()
    best_protos = som_obj.sorted_proto_idxs[:,0]
    print(best_protos)
    sorted_cutouts = np.argsort(som_obj.data_map[range(som_model.number_of_images), best_protos])
    print(sorted_cutouts)
    counter = 0
    cutouts = []
    for idx in sorted_cutouts:
        if counter >= n_cutouts:
            break
        proto_idx = best_protos[idx]
        if proto_idx == prototype.proto_id:
            distance = som_obj.data_map[idx][proto_idx]
            dir_name = os.path.join('data', som_model.training_dataset_name, 'proto'+str(proto_idx))
            if not os.path.exists(os.path.join(settings.MEDIA_ROOT, dir_name)):
                os.makedirs(os.path.join(settings.MEDIA_ROOT, dir_name))
            cutout_filename = os.path.join(dir_name,
                                           "cutout{0}.png".format(idx))
            plot_image(return_cutout(som_model.data_path.path, idx),
                       os.path.join(settings.MEDIA_ROOT, cutout_filename))

            with open(som_model.csv_path.path) as csv_file:
                catalog = csv.DictReader(csv_file)
                ra, dec = get_sky_coords(catalog, idx)
            cutout_model = som.models.SomCutout(
                som=som_model,
                ra=ra,
                dec=dec,
                csv_path=som_model.csv_path,
                csv_row_idx=idx,
                closest_prototype=prototype,
                distance=distance,
            )
            cutout_model.image.name = cutout_filename
            cutout_model.save()
            cutouts.append(cutout_model)
            counter += 1
    return cutouts


def create_som_histogram(som_model):
    som_obj = som_model.load_som_obj()
    bmu_distances = np.max(som_obj.data_map, axis=1)
    plot_histogram(bmu_distances, som_model.histogram.path)


def plot_histogram(bmu_distances, save_path, xmax=200, bins=100):
    fig = plt.figure()
    fig.set_size_inches(9, 4.5)
    ax = fig.add_subplot(111)
    bins = ax.hist(bmu_distances, bins=bins, histtype='step', linewidth=3)
    height = max(bins[0])
    plt.xlim(0, xmax)
    plt.yscale('log')
    plt.ylim(0.6, height)
    plt.xlabel('Summed Euclidian (SE) distance to best matching prototype')
    plt.ylabel('Number of radio-sources per bin')
    plt.tight_layout()
    plt.savefig(save_path, transparent=True)



def create_cutout_models(som_model, catalog):
    """
    Generate images and database entries for the map-specific dataset
    Furthermore, save the distance to all prototypes to the database
    :param som_model: The SOM database model that belongs to these cutouts
    :param catalog: A csv file containing the sky position of the image objects
    :return:
    """
    print("Generating all cutout images and saving them to the database (this is going to take forever...")
    # Save and plot the cutouts
    som_obj = som_model.load_som_obj()
    best_protos = som_obj.sorted_proto_idxs[:,0]
    print(best_protos)
    for cutout_idx in range(som_model.number_of_images):
        best_prototype = som.models.Prototype.objects.get(proto_id=best_protos[cutout_idx])
        distance = som_obj.data_map[cutout_idx][best_protos[cutout_idx]]
        print("Cutout {idx} from {total}...".format(idx=cutout_idx, total=som_model.number_of_images))
        print("Best prototype: {proto}. Distance: {dist}".format(proto=best_protos[cutout_idx], dist=distance))
        cutout_filename = os.path.join('data', som_model.training_dataset_name,
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
            closest_prototype=best_prototype,
            distance=distance
        )
        cutout_model.image.name = cutout_filename
        cutout_model.save()

        # Save the distances to each prototype for this cutout
        #print("Saving distances to all {no_p} prototypes for cutout {no_c}".format(
        #    no_p=mapping.shape[1], no_c=cutout_idx))
        #for proto_idx in sorted_proto_idxs[cutout_idx]:
        #    distance = mapping[cutout_idx][proto_idx]
        #    prototype = som.models.Prototype.objects.get(proto_id=proto_idx)
        #    som.models.Distance.objects.create(
        #        distance=distance,
        #        prototype=prototype,
        #        cutout=cutout_model
        #    )
    print("...done.")


def create_outliers(som_id, n_outliers):
    """
    Generate images and database entries for the outliers of the map
    :param som_model: The SOM database model that belongs to these outliers
    :param mapping: An array containing the distances of the cutouts to each prototype
    :param catalog: A csv file containing the sky position of the image objects
    :param n_outliers: The number of outliers that should be saved
    :return:
    """
    som_model = som.models.SOM.objects.get(id=som_id)
    som_obj = som_model.load_som_obj()
    best_protos = som_obj.sorted_proto_idxs[:, 0]
    best_distances = som_obj.data_map[range(som_model.number_of_images), best_protos]
    sorted_best_distance_idxs = np.argsort(best_distances)
    farest_distance_idxs = sorted_best_distance_idxs[-n_outliers:]
    print("Generating outliers...")
    counter = 0
    outliers = []
    for outlier_idx in farest_distance_idxs:
        print("Outlier {idx} from {total}. Distance: {dist}".format(idx=counter, total=n_outliers, dist=best_distances[outlier_idx]))
        outlier_filename = os.path.join('outliers', som_model.training_dataset_name,
                                        "outlier{0}.png".format(outlier_idx))
        plot_image(return_cutout(som_model.data_path.path, outlier_idx),
                   os.path.join(settings.MEDIA_ROOT, outlier_filename))
        with open(som_model.csv_path.path) as csv_file:
            catalog = csv.DictReader(csv_file)
            ra, dec = get_sky_coords(catalog, outlier_idx)
        outlier_model = som.models.Outlier(
            som=som_model,
            ra=ra,
            dec=dec,
            csv_path=som_model.csv_path,
            csv_row_idx=outlier_idx,
            distance=best_distances[outlier_idx]
        )
        outlier_model.image.name = outlier_filename
        outlier_model.save()
        outliers.append(outlier_model)
        counter += 1
    return outliers


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
