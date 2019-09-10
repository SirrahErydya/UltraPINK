from django.core.management.base import BaseCommand
from som.models import SOM, Prototype, SomCutout
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import image as mpimg
from matplotlib import gridspec as gridspec
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Add outliers to database'

    def add_arguments(self, parser):
        parser.add_argument('som_id', type=int, default=0)

    def handle(self, *args, **options):
        som_model = SOM.objects.get(id=options['som_id'])
        prototypes = Prototype.objects.filter(som=som_model).order_by('y', 'x')
        figure = plt.figure(figsize=(som_model.som_width, som_model.som_height), frameon=False)
        grid = gridspec.GridSpec(som_model.som_width, som_model.som_height)
        grid.update(wspace=0.05, hspace=0.05)
        i = 0
        for prototype in prototypes:
            axis = plt.subplot(grid[i])
            axis.set_axis_off()
            axis.imshow(mpimg.imread(prototype.image.path))
            i += 1
        plt.subplots_adjust(wspace=0, hspace=0)
        figure.savefig(os.path.join(settings.MEDIA_ROOT, 'prototypes', som_model.training_dataset_name, 'protos.png'))