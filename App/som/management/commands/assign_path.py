from django.core.management.base import BaseCommand
from django.conf import settings
import os
from som.som_postprocessing import SOM, plot_image, return_cutout
import som.models
import csv
import numpy as np
from django.core.files import File


class Command(BaseCommand):
    help = 'Reassigns the path attributes of a SOM'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str)
        parser.add_argument('filename', type=str)
        parser.add_argument('som_id', type=int, default=0)

    def handle(self, *args, **options):
        path = options['path']
        som_model = som.models.SOM.objects.get(id=options['som_id'])
        if path == 'data':
            filename = os.path.join(settings.BIN_DIR, options['filename'] + '.bin')
            som_model.data_path = filename
            som_model.save()
        else:
            raise NotImplementedError("Fix this, Fenja")
