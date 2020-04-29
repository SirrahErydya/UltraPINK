"""
This is a collection of functions to automatically create database entries with SOM components
:author: Fenja Kollasch
"""
import som.models as smodels
import pinkproject.models as pmodels
import os
from django.conf import settings
from django.db import IntegrityError
from PIL import Image
from io import BytesIO
import base64
import numpy as np
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
    save_path = os.path.join('projects', dataset_model.project.project_name, "soms", som_name)
    os.makedirs(save_path, exist_ok=True)
    full_path = os.path.join(save_path, "{0}.npy".format(som_name))
    np.save(full_path, np_som)
    # Create SOM model
    som_model = smodels.SOM(
        som_name=som_name,
        som_width=np_som.shape[0],
        som_height=np_som.shape[1],
        som_depth=1, # By now, only 2d Soms
        layout=pink_som.get_som_layout(),
        number_of_neurons=np.prod(np_som.shape),
        dataset=dataset_model
    )
    som_model.som_file = os.path.join(full_path)
    som_model.save()
    create_prototype_models(som_model)
    print("...done.")
    #create_som_histogram(som_model)
    return som_model


def create_dataset_models(dataset_name, descr, numpy_data, project, csv_file=None):
    save_path = os.path.join('projects', project.project_name, "datasets", dataset_name)
    os.makedirs(save_path, exist_ok=True)
    full_path = os.path.join(save_path, "{0}.npy".format(dataset_name))
    np.save(full_path, numpy_data)
    dataset = pmodels.Dataset(
        project=project,
        dataset_name=dataset_name,
        description=descr,
        length=len(numpy_data),
        csv_path=csv_file
    )
    dataset.data_path = full_path
    dataset.save()
    return dataset


def create_prototype_models(som_model):
    """
    Generate images and database entries for each prototype in the map
    :param som_model: The SOM database model that belongs to these prototypes
    """
    np_som = np.load(som_model.som_file.path)
    for y in range(som_model.som_height):
        for x in range(som_model.som_width):
            np_img = np_som[y][x]
            img_link = np_image_link(np_img)
            prototype = smodels.Prototype.objects.create(
                som = som_model,
                x = x,
                y = y,
                z = 1,
                number_of_fits = 0,
                image=img_link
            )
    print("...done.")


def save_heatmap(heatmap, path):
    figure = plt.figure(frameon=False)
    axis = plt.Axes(figure, [0., 0., 1., 1.])
    axis.set_axis_off()
    figure.add_axes(axis)
    for y in range(heatmap.shape[0]):
        for x in range(heatmap.shape[1]):
            axis.text(x, y, heatmap[y][x], ha="center", va="center", color="w")
    axis.imshow(heatmap)
    figure.savefig(path)


def create_datapoint_models(np_data, som, index):
    img_link = np_image_link(np_data) # TODO: Non-image data points?
    dp = smodels.DataPoint(
        dataset=som.dataset,
        index=index,
        image=img_link
        # TODO: Add meta info
    )
    try:
        dp.save()
    except IntegrityError:
        dp = None


def np_image_link(np_img):
    pil_image = Image.fromarray(np_img * 255)
    pil_image = pil_image.convert('L')
    data = BytesIO()
    pil_image.save(data, 'PNG')
    data64 = base64.b64encode(data.getvalue())
    return u'data:img/png;base64,' + data64.decode('utf-8')


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
