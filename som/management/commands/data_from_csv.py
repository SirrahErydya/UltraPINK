import csv
from django.core.management.base import BaseCommand, CommandError
from som.models import SomEntry
from tqdm import tqdm


class Command(BaseCommand):
    help = 'Adds data rows from a csv file'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str)

    def handle(self, *args, **options):
        """
        Create models for every SOM entry by parsing CSV
        :param filename: name of the csv file
        :return:
        """
        filename = options['filename']
        with open(filename, 'r') as file:
            reader = csv.DictReader(file)
            print("Creating database models for all entries from", filename)
            for row in tqdm(reader):
                _, entry = SomEntry.objects.get_or_create(
                    source_name=row['Source_Name'],
                    s_code=row['S_Code'],
                    mosaic_id=row['Mosaic_ID'],
                    isl_id=row['Isl_id'],
                    ra=row['RA'],
                    e_ra=row['E_RA'],
                    e_ra_tot=row['E_RA_tot'],
                    dec=row['DEC'],
                    e_dec=row['E_DEC'],
                    e_dec_tot=row['E_DEC_tot'],
                    peak_flux=row['Peak_flux'],
                    e_peak_flux=row['E_Peak_flux'],
                    e_peak_flux_tot=row['E_Peak_flux_tot'],
                    total_flux=row['Total_flux'],
                    e_total_flux=row['E_Total_flux'],
                    e_total_flux_tot=row['E_Total_flux_tot'],
                    maj=row['Maj'],
                    e_maj=row['E_Maj'],
                    min=row['Min'],
                    e_min=row['E_Min'],
                    pa=row['PA'],
                    e_pa=row['E_PA'],
                    isl_rms=row['Isl_rms'],
                    median_local_sigma=row['median_local_sigma'],
                    mean_local_sigma=row['mean_local_sigma'],
                    closest_prototype_x=row['Closest_prototype_x'],
                    closest_prototype_y=row['Closest_prototype_y'],
                    cutout_index=row['cutout_index']
            )
