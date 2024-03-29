"""
Create, train and import SOMs with PINK
:author: Fenja Kollasch
"""
import pink
import math
from som.models import Prototype, DataPoint, Label
from django.conf import settings
import numpy as np
import csv
import os
from tqdm import tqdm
import UltraPINK.create_database_entries as dbe


def train(data, som_dim, layout, number_of_rotations, epochs):
    """
    Create (and train) a new SOM for a given data set
    :param data: The path to the raw data
    :param som_dim: Dimensions of the resulting SOM
    :param layout: The SOM layout (hexagonal or cartesian)
    :param number_of_rotations: Number of rotations
    :param epochs: Training epochs
    :return: A trained SOM object
    """
    print(pink.__version__)
    neuron_dim = int(data.shape[1] / math.sqrt(2.0) * 2.0)
    euclid_dim = int(data.shape[1] * math.sqrt(2.0) / 2.0)
    width, height, depth = som_dim
    if layout == 'cartesian-2d':
        np_som = np.zeros((int(width), int(height), neuron_dim, neuron_dim)).astype(np.float32)
    elif layout == 'hexagonal-2d':
        #@ Todo: Only for square-shaped 2D hex soms
        radius = (int(width) - 1) / 2
        number_of_neurons = int(int(width) * int(height) - radius * (radius + 1))
        np_som = np.random.rand(number_of_neurons, neuron_dim, neuron_dim).astype(np.float32)
    else:
        raise AttributeError("Invalid layout: {0}".format(layout))
    som = pink.SOM(np_som, som_layout=layout)

    trainer = pink.Trainer(som, number_of_rotations=int(number_of_rotations), euclidean_distance_dim=euclid_dim,
                           distribution_function=pink.GaussianFunctor(1.1, 0.2))
    print("Start training...")
    for e in range(int(epochs)):
        print("Epoch {0}".format(e+1))
        for point in tqdm(data):
            point = point.astype(np.float32)
            if point.max() > 1:
                point = point/255
            trainer(pink.Data(point))
    trainer.update_som()
    return som


def import_som(project, dataset_name, som_binfile, mapping_binfile, data_binfile=None, csv_file=None):
    bin_dir = os.path.join(settings.BIN_DIR, dataset_name)
    data_dir = os.path.join(settings.DATA_DIR, dataset_name)
    fs = FileSystemStorage()
    if data_binfile is not None:
        data_file_name = fs.save(os.path.join(bin_dir, data_binfile.name), data_binfile)
    else:
        raise FileNotFoundError('You need a binary file containing the images.')
    som_file_name = fs.save(os.path.join(bin_dir, som_binfile.name), som_binfile)
    mapping_file_name = fs.save(os.path.join(bin_dir, mapping_binfile.name), mapping_binfile)
    csv_file_name = fs.save(os.path.join(data_dir, csv_file.name), csv_file)
    som_obj_path = os.path.join(settings.BIN_DIR, dataset_name, 'som_' + dataset_name + '.pkl')

    som_obj = SOM_obj(dataset_name, som_file_name, mapping_file_name, som_obj_path)
    som_obj.save()

    # Creating directories
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'prototypes', som_obj.training_dataset_name), exist_ok=True)
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'outliers', som_obj.training_dataset_name), exist_ok=True)

    som_model = db.create_som_model(project, som_file_name, mapping_file_name, data_file_name, csv_file_name, som_obj)

    # Create prototype entries and save the plots
    db.create_prototype_models(som_model, som_obj.data_som)

    return som_model.id


def map_som(som_model):
    np_som = np.load(som_model.som_file.path, allow_pickle=True)
    np_data = np.load(som_model.dataset.data_path.path, allow_pickle=True)
    euclidean_dim = int(np_data.shape[1] * math.sqrt(2.0) / 2.0)
    layout = som_model.layout
    som = pink.SOM(np_som, som_layout=layout)
    mapper = pink.Mapper(som, euclidean_distance_dim=euclidean_dim)
    map_table = np.zeros((np_data.shape[0], np_som.shape[0]*np_som.shape[1]))
    heatmap = np.zeros((np_som.shape[0], np_som.shape[1]))
    if layout == 'hexagonal-2d':
        map_table = np.zeros((np_data.shape[0], np_som.shape[0]))
        heatmap = np.zeros((som_model.som_width, som_model.som_width))
    for i in tqdm(range(np_data.shape[0])):
        point = np_data[i].astype(np.float32)
        if point.max() > 1:
            point = point/255
        distances, _ = mapper(pink.Data(point))
        map_table[i] = distances
        best_proto = np.argmin(distances)
        if layout == 'cartesian-2d':
            proto_x = best_proto % np_som.shape[1]
            proto_y = int((best_proto - proto_x) / np_som.shape[0])

        elif layout == 'hexagonal-2d':
            proto_x = best_proto % som_model.som_width
            proto_y = int((best_proto - proto_x) / som_model.som_width)
            cols_allowed = int(som_model.som_width - (np.abs(proto_y - np.floor(som_model.som_width / 2))))
            while proto_x >= cols_allowed:
                proto_y += 1
                proto_x -= cols_allowed
                cols_allowed = int(som_model.som_width - (np.abs(proto_y - np.floor(som_model.som_width / 2))))
        heatmap[proto_y][proto_x] += 1
        dbe.create_datapoint_models(np_data[i], som_model, i, best_proto)
    return map_table, heatmap


def get_data(data):
    """
    Get the training data as a numpy array
    :param data: The uploaded data file
    """
    file_ending = data.name.split('.')[-1]
    if file_ending == 'npy':
        data = np.load(data, allow_pickle=True)
        np.random.shuffle(data)
        data = np.squeeze(data)
    else:
        raise TypeError("It is currently not possible to process {0} files.".format(file_ending))
    return data


def get_distances(som, prototype=None):
    distance_file = np.load(som.mapping_file)
    if prototype:
        proto_id = prototype.som.som_width * prototype.y + prototype.x
        distances = distance_file[:, proto_id]
        return distances
    return distance_file


def get_protos_from_db(proto_ids):
    proto_ids = [int(''.join(filter(lambda i: i.isdigit(), proto_id))) for proto_id in proto_ids]
    return [Prototype.objects.get(id=proto_id) for proto_id in proto_ids]


def label_protos(protos, label):
    protos = get_protos_from_db(protos)
    try:
        label_model = Label.objects.get(name=label, som=protos[0].som_id)
    except Label.DoesNotExist:
        r = np.random.randint(0, 255)
        g = np.random.randint(0, 255)
        b = np.random.randint(0, 255)
        label_model = Label(
            som=protos[0].som,
            name=label,
            color_r=r,
            color_g=g,
            color_b=b
        )
        label_model.save()
    for proto in protos:
        proto.label = label_model
        proto.save()


def label_cutouts(cutout_ids, label):
    for cutout_id in cutout_ids:
        cutout = DataPoint.objects.get(id=cutout_id)
        cutout.label = label
        cutout.save()


def export_catalog(entries, filename):
    with open(os.path.join(settings.DATA_DIR, filename + '.csv'), 'w') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', "RA", 'Dec', 'Clostest prototype', 'Label', 'Image File'])
        for cutout in entries:
            try:
                clostest_proto = cutout.closest_prototype.id
            except AttributeError:
                clostest_proto = ""
            writer.writerow([cutout.id, cutout.ra, cutout.dec, clostest_proto, cutout.label, cutout.image.path])