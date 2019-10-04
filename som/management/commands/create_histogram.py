from django.core.management.base import BaseCommand
from som.models import SOM
import som.create_database_entries as dbe


class Command(BaseCommand):
    help = 'Create histogram'

    def add_arguments(self, parser):
        parser.add_argument('som_id', type=int, default=0)

    def handle(self, *args, **options):
        som_model = SOM.objects.get(id=options['som_id'])
        dbe.create_som_histogram(som_model)

