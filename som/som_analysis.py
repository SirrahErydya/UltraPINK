"""
These functions perform basic analysis operations on a SOM
:author: Fenja Kollasch
"""
from som.models import Prototype, SomCutout, Distance
import numpy as np


def get_best_fits(proto, n_fits=10):
    prototype = Prototype.objects.get(proto_id=proto)
    dists = Distance.objects.filter(prototype=prototype).order_by('distance')
    return [dists[i].cutout for i in range(n_fits)]


def get_best_fits_to_protos(prototypes, n_fits=10):
    cutouts = list(SomCutout.objects.all())
    avg_distances = []
    for cutout in cutouts:
        distances = np.asarray([Distance.objects.get(prototype=proto, cutout=cutout).distance for proto in prototypes])
        avg_distances.append(np.mean(distances))
    assert len(avg_distances) == len(cutouts)
    cutout_indices = np.argsort(np.asarray(avg_distances))
    cutouts = [cutouts[cutout_indices[i]] for i in range(n_fits)]
    return cutouts


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