from django.core.management.base import BaseCommand
from som.models import SOM, Prototype, SomCutout
import numpy as np
from matplotlib import pyplot as plt
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Add outliers to database'

    def add_arguments(self, parser):
        parser.add_argument('som_id', type=int, default=0)

    def handle(self, *args, **options):
        som_model = SOM.objects.get(id=options['som_id'])
        prototypes = Prototype.objects.filter(som=som_model).order_by('y', 'x')
        heatmap = np.ndarray((som_model.som_width, som_model.som_height))
        figure = plt.figure(frameon=False)
        axis = plt.Axes(figure, [0., 0., 1., 1.])
        axis.set_axis_off()
        figure.add_axes(axis)
        for prototype in prototypes:
            no_fits = SomCutout.objects.filter(closest_prototype=prototype).count()
            heatmap[prototype.y][prototype.x] = no_fits
            axis.text(prototype.x, prototype.y, no_fits, ha="center", va="center", color="w")
        axis.imshow(heatmap)
        figure.savefig(os.path.join(settings.MEDIA_ROOT, 'cutouts', som_model.training_dataset_name, 'heatmap.png'))
