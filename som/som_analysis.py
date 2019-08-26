"""
These functions perform basic analysis operations on a SOM
:author: Fenja Kollasch
"""
from som.models import Prototype, SomCutout, Distance
import numpy as np


def get_best_fits(proto, n_fits=10):
    prototype = Prototype.objects.get(proto_id=proto)
    dists = Distance.objects.filter(prototype=prototype).order_by('distance')
    return [dist.cutout for dist in dists]


def get_best_fits_to_protos(proto_ids, n_fits=10):
    prototypes = [Prototype.objects.get(proto_id=proto_id) for proto_id in proto_ids]
    cutouts = SomCutout.objects.all()
    avg_distances = []
    for cutout in cutouts:
        distances = np.asarray([Distance.objects.get(prototype=proto, cutout=cutout) for proto in prototypes])
        avg_distances.append(np.mean(distances))
    assert len(avg_distances) == len(cutouts)
    cutout_indices = np.argsort(np.asarray(avg_distances))[:n_fits]
    return [cutouts[i] for i in cutout_indices]
