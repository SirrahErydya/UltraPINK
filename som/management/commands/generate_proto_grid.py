from django.core.management.base import BaseCommand
from som.models import SOM, Prototype, DataPoint
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import image as mpimg
from matplotlib import gridspec as gridspec
from django.conf import settings
import os
from UltraPINK import create_database_entries as dbe

class Command(BaseCommand):
    help = 'Generate protoype map'

    def add_arguments(self, parser):
        parser.add_argument('som_id', type=int, default=0)

    def handle(self, *args, **options):
        som_model = SOM.objects.get(id=options['som_id'])
        dbe.save_prototype_grid(som_model, os.path.join(settings.MEDIA_ROOT, 'protos.png'))
