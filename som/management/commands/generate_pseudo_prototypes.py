from django.core.management.base import BaseCommand, CommandError
from som.models import Prototype
from tqdm import tqdm


class Command(BaseCommand):
    def handle(self, *args, **options):
        for i in tqdm(range(10)):
            for j in tqdm(range(10)):
                _, entry = Prototype.objects.get_or_create(
                    x=i, y=j
                )
