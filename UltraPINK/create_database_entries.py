"""
This is a collection of functions to automatically create database entries with SOM components
:author: Fenja Kollasch
"""
import som.models as smodels
import pinkproject.models as pmodels
import os
import numpy as np
from django.conf import settings
import matplotlib.pyplot as plt
import csv


def create_som_model(som_name, pink_som, dataset_model):
    """
    Create a database model for a complete SOM capsuling the data
    :param som_name: The Name for the SOM
    :param pink_som: The PINK object representing the trained SOM
    :param dataset_model: The Dataset which trained the SOM
    :return: A Django Database model of the given SOM
    """
    print("Creating SOM model...")
    np_som = np.array(pink_som)
    save_path = os.path.join(dataset_model.project.project_name, "soms", som_name)
    os.makedirs(save_path, exist_ok=True)
    full_path = os.path.join(save_path, "{0}.npy".format(som_name))
    np.save(full_path, np_som)
    # Create SOM model
    som_model = smodels.SOM.objects.create(
        som_name=som_name,
        som_width=np_som.shape[0],
        som_height=np_som.shape[1],
        som_depth=np_som.shape[2],
        layout=pink_som.get_som_layout(),
        number_of_neurons=np.prod(np_som.shape),
        som_file=full_path,
        dataset=dataset_model,
        current=False
    )
    print("...done.")
    #create_som_histogram(som_model)
    return som_model


def create_dataset_models(dataset_name, numpy_data, project, csv_file=None):
    save_path = os.path.join(project.project_name, "datasets", dataset_name)
    os.makedirs(save_path, exist_ok=True)
    full_path = os.path.join(save_path, "{0}.npy".format(dataset_name))
    np.save(full_path, numpy_data)
    dataset = pmodels.Dataset.objects.create(
        project=project,
        dataset_name=dataset_name,
        length=len(numpy_data),
        data_path=full_path,
        csv_path=csv_file
    )
    return dataset


def create_prototype_models(som_model, prototypes):
    """
    Generate images and database entries for each prototype in the map
    :param som_model: The SOM database model that belongs to these prototypes
    :param prototypes: All prototypes as numpy arrays
    """
    som_obj = som_model.load_som_obj()
    best_protos = som_obj.sorted_proto_idxs[:,0]

    heatmap = np.ndarray((som_model.som_width, som_model.som_height))
    for x in range(som_model.som_height):
        for y in range(som_model.som_width):
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
                histrogram_name = os.path.join('prototypes', som_model.training_dataset_name,
                                                          'histogram{x}{y}{z}.png'.format(x=x, y=y, z=z))
                proto_model.histogram.name = histrogram_name
                proto_model.save()

                #bmu_distances = som_obj.data_map[:proto_model.proto_id]
                #plot_histogram(bmu_distances, histrogram_name)
                heatmap[y][x] = number_of_fits

    plt.subplots_adjust(wspace=0, hspace=0)
    heatmap_file = os.path.join('prototypes', som_model.training_dataset_name, 'heatmap.png')
    save_heatmap(heatmap, heatmap_file)
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
    sorted_cutouts = np.argsort(som_obj.data_map[range(som_model.number_of_images), best_protos])
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
            cutout_model = som.models.DataPoint(
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
    file_name = os.path.join('data', som_model.training_dataset_name, 'histogram.png')
    plot_histogram(bmu_distances, os.path.join(settings.MEDIA_ROOT, file_name))
    som_model.histogram.name = file_name
    som_model.save()


def plot_histogram(bmu_distances, save_path, bins=100):
    plt.hist(bmu_distances, bins=bins)
    plt.xlabel('Summed Euclidian (SE) distance to best matching prototype')
    plt.ylabel('Number of radio-sources per bin')
    plt.tight_layout()
    plt.savefig(os.path.join(settings.MEDIA_ROOT,save_path), transparent=True)
    plt.close()


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
        cutout_model = som.models.DataPoint(
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
