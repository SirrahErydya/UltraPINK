"""
These functions perform basic analysis operations on a SOM
:author: Fenja Kollasch
"""
from som.models import Prototype, SomCutout
from django.db.models import Q
from django.conf import settings
import numpy as np
import csv
import os
import som.create_database_entries as dbe


def get_best_fits(proto, n_fits=10):
    prototype = Prototype.objects.get(proto_id=proto)
    cutouts = SomCutout.objects.filter(closest_prototype=prototype).order_by('distance')[:n_fits]
    if len(cutouts) < n_fits:
        return dbe.create_cutouts_for_prototype(prototype, n_fits)
    else:
        return list(cutouts)


# def get_best_fits_to_protos(prototypes, n_fits=10):
#     cutouts = list(SomCutout.objects.all())
#     avg_distances = []
#     for cutout in cutouts:
#         distances = np.asarray([Distance.objects.get(prototype=proto, cutout=cutout).distance for proto in prototypes])
#         avg_distances.append(np.mean(distances))
#     assert len(avg_distances) == len(cutouts)
#     cutout_indices = np.argsort(np.asarray(avg_distances))
#     cutouts = [cutouts[cutout_indices[i]] for i in range(n_fits)]
#     return cutouts


def get_protos(proto_ids):
    return [Prototype.objects.get(proto_id=proto_id) for proto_id in proto_ids]


def label_protos(proto_ids, label):
    for proto_id in proto_ids:
        proto = Prototype.objects.get(proto_id=proto_id)
        proto.label = label
        proto.save()


def label_cutouts(cutout_ids, label):
    for cutout_id in cutout_ids:
        cutout = SomCutout.objects.get(id=cutout_id)
        cutout.label = label
        cutout.save()


def export_catalog(cutout_ids, filename):
    if len(cutout_ids) == 0:
        cutouts = SomCutout.objects.filter(~Q(label=''))
    else:
        cutouts = [SomCutout.objects.get(id='cutout_id') for cutout_id in cutout_ids]
    with open(os.path.join(settings.DATA_DIR, filename + '.csv'), 'w') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', "RA", 'Dec', 'Clostest prototype', 'Label', 'Image File'])
        for cutout in cutouts:
            writer.writerow([cutout.id, cutout.ra, cutout.dec, cutout.closest_prototype.id, cutout.label, cutout.image.path])