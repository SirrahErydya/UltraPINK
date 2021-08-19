"""
This is a collection of functions to automatically create database entries with SOM components
:author: Fenja Kollasch
"""
import som.models as smodels
import pinkproject.models as pmodels
import os
from django.conf import settings
from django.db import IntegrityError
from PIL import Image, ImageDraw
from io import BytesIO
import base64
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec as gridspec
from matplotlib import image as mpimg
import csv


def create_som_model(som_name, pink_som, som_dims, dataset_model):
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
        som_width=int(som_dims[0]),
        som_height=int(som_dims[1]),
        som_depth=int(som_dims[2]),
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
    som_idx = 0 # only relevant for hex-maps
    for y in range(som_model.som_height):
        for x in range(som_model.som_width):
            if som_model.layout == 'cartesian-2d':
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
            elif som_model.layout == 'hexagonal-2d':
                cols_allowed = int(som_model.som_width - (np.abs(y - np.floor(som_model.som_width / 2))))
                print(cols_allowed)
                if x < cols_allowed and som_idx < np_som.shape[0]:
                    q = np.abs(int(y - np.floor(som_model.som_width / 2))) + x
                    r = y
                    np_img = np_som[som_idx]
                    img_link = np_image_link(np_img, layout=som_model.layout)
                    prototype = smodels.Prototype.objects.create(
                        som=som_model,
                        x=q,
                        y=r,
                        z=1,
                        number_of_fits=0,
                        image=img_link
                    )
                    som_idx +=1
    print("...done.")


def save_prototype_grid(som_model, path):
    """
    Create an image of the whole SOM grid
    :param som_model: The SOM database model
    """
    prototypes = smodels.Prototype.objects.filter(som=som_model)

    if som_model.layout == 'cartesian-2d':
        figure = plt.figure(figsize=(10, 10), frameon=False)
        grid = gridspec.GridSpec(som_model.som_width, som_model.som_height, wspace=0.0, hspace=0.0,
                                 bottom=0, top=1, left=0, right=1)
        i = 0
        for prototype in prototypes:
            axis = plt.subplot(grid[i])
            axis.set_axis_off()
            axis.set_aspect('equal')
            axis.imshow(mpimg.imread(prototype.image), cmap='gray')
            i += 1
        plt.subplots_adjust(wspace=0.0, hspace=0.0)
        figure.savefig(path)
        plt.close()
    elif som_model.layout == 'hexagonal-2d':
        som_width = som_model.som_width  # assume squared som
        np_som = np.load(som_model.som_file.path)
        neuron_dim = np_som.shape[1]
        border = 1
        image = Image.new('RGB', (int(som_width * neuron_dim + (som_width - 1) * border),
                                  int(neuron_dim + (som_width - 1) * (0.77 * neuron_dim) + (som_width - 2) * border)),
                          (255, 255, 255))
        som_idx = 0
        for row in range(som_width):
            cols_allowed = int(som_width - (np.abs(row - np.floor(som_width / 2))))
            x_pos = int(((som_width - cols_allowed) / 2) * neuron_dim)
            y_pos = int(row * (0.77 * neuron_dim))
            if row != 0 and row != som_width - 1:
                y_pos += border
            print("X:", x_pos)
            print("Y:", y_pos)
            for col in range(cols_allowed):
                if som_idx < np_som.shape[0]:
                    pil_image = Image.fromarray(np_som[som_idx] * 255)
                    pil_image = pil_image.convert('L')
                    mask = Image.new('RGBA', pil_image.size)
                    d = ImageDraw.Draw(mask)
                    d.polygon(((neuron_dim / 2, 0), (neuron_dim, neuron_dim / 4), (neuron_dim, 3 * neuron_dim / 4),
                               (neuron_dim / 2, neuron_dim), (0, 3 * neuron_dim / 4), (0, neuron_dim / 4)), fill='#FFF')
                    image.paste(pil_image, (x_pos, y_pos), mask)
                    x_pos += neuron_dim
                    if col != cols_allowed - 1:
                        x_pos += border
                    som_idx += 1
        image.save(path)


def save_heatmap(heatmap, path):
    figure = plt.figure(figsize=heatmap.shape, frameon=False)
    axis = plt.Axes(figure, [0., 0., 1., 1.])
    axis.set_axis_off()
    figure.add_axes(axis)
    for y in range(heatmap.shape[0]):
        for x in range(heatmap.shape[1]):
            axis.text(x, y, heatmap[y][x], ha="center", va="center", color="w")
    axis.imshow(heatmap)
    figure.savefig(path)
    plt.close()


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


def np_image_link(np_img, layout='cartesian-2d'):
    pil_image = Image.fromarray(np_img * 255)
    pil_image = pil_image.convert('L')
    img = pil_image
    if layout == 'hexagonal-2d':
        neuron_dim = pil_image.width
        mask = Image.new('RGBA', pil_image.size)
        d = ImageDraw.Draw(mask)
        d.polygon(((neuron_dim / 2, 0), (neuron_dim, neuron_dim / 4), (neuron_dim, 3 * neuron_dim / 4),
                   (neuron_dim / 2, neuron_dim), (0, 3 * neuron_dim / 4), (0, neuron_dim / 4)), fill='#FFF')
        img = Image.new('RGBA', pil_image.size)
        img.paste(pil_image, (0, 0), mask)

    data = BytesIO()
    img.save(data, 'PNG')
    data64 = base64.b64encode(data.getvalue())
    return u'data:img/png;base64,' + data64.decode('utf-8')


def plot_histogram(bmu_distances, save_path, bins=100):
    # TODO: Find out why this function goes bananas
    plt.hist(bmu_distances, bins=bins)
    plt.xlabel('Summed Euclidian (SE) distance to best matching prototype')
    plt.ylabel('Number of sources per bin')
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
