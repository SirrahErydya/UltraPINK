"""
Create, train and import SOMs with PINK
:author: Fenja Kollasch
"""
import pink
import math
from som.models import Prototype, DataPoint
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
    neuron_dim = int(data.shape[1] / math.sqrt(2.0) * 2.0)
    euclid_dim = int(data.shape[1] * math.sqrt(2.0) / 2.0)
    width, height, depth = som_dim
    if layout == 'cartesian-2d':
        np_som = np.zeros((int(width), int(height), neuron_dim, neuron_dim)).astype(np.float32)
    else:
        raise NotImplementedError("Only cartesian layouts by now")
    som = pink.SOM(np_som, neuron_layout=layout)

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
    np_som = np.load(som_model.som_file.path)
    np_data = np.load(som_model.dataset.data_path.path)
    euclidean_dim = int(np_data.shape[1] * math.sqrt(2.0) / 2.0)
    layout = som_model.layout
    som = pink.SOM(np_som, som_layout=layout)
    mapper = pink.Mapper(som, euclidean_distance_dim=euclidean_dim)
    map_table = np.zeros((np_data.shape[0], np_som.shape[0]*np_som.shape[1]))
    heatmap = np.zeros((np_som.shape[0], np_som.shape[1]))
    for i in tqdm(range(np_data.shape[0])):
        point = np_data[i].astype(np.float32)
        if point.max() > 1:
            point = point/255
        distances, _ = mapper(pink.Data(point))
        map_table[i] = distances
        best_proto = np.argmin(distances)
        proto_x = best_proto % np_som.shape[1]
        proto_y = int((best_proto - proto_x)/np_som.shape[0])
        heatmap[proto_y][proto_x] += 1
        dbe.create_datapoint_models(np_data[i], som_model, i)
    return map_table, heatmap


def get_data(data):
    """
    Get the training data as a numpy array
    :param data: The uploaded data file
    """
    file_ending = data.name.split('.')[-1]
    if file_ending == 'npy':
        data = np.load(data)
        np.random.shuffle(data)
        data = np.squeeze(data)
    else:
        raise TypeError("It is currently not possible to process {0} files.".format(file_ending))
    return data


def get_distances(proto):
    prototype = Prototype.objects.get(id=proto)
    distance_file = np.load(prototype.som.mapping_file)
    match_file = np.argmin(distance_file, axis=1)
    proto_id = prototype.som.som_width * prototype.y + prototype.x
    data_indices = np.where(match_file == proto_id)[0]
    distances = distance_file[data_indices, proto_id]
    return distances

# def get_best_fits(proto, n_fits=10):
#    prototype = Prototype.objects.get(proto_id=proto)
#    cutouts = DataPoint.objects.filter(closest_prototype=prototype).order_by('distance')[:n_fits]
#    if len(cutouts) < n_fits:
#        return dbe.create_cutouts_for_prototype(prototype, n_fits)
#    else:
#        return list(cutouts)


def get_protos(proto_ids):
    return [Prototype.objects.get(proto_id=proto_id) for proto_id in proto_ids]


def label_protos(proto_ids, label):
    for proto_id in proto_ids:
        p_id = int(''.join([i for i in proto_id if i.isdigit()]))
        proto = Prototype.objects.get(id=p_id)
        proto.label = label
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