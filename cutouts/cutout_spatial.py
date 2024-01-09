from UltraPINK import coreconcepts as cc
import numpy as np
from som import models
import csv
from astropy import coordinates as ac
from astropy.units import UnitsError

def cutout_distsort(cutout_obj, som):
    all_db_cutouts = models.DataPoint.objects.filter(som=som)
    cutouts_sorted = []
    # Mergesort or something. Idk, I'm not efficient
    for db_cutout in all_db_cutouts:
        if db_cutout.id == cutout_obj.db_obj.id:
            continue
        cutout_meta = get_cutout_meta(som, db_cutout)
        current_cutout = create_cutout_obj(cutout_meta, som, db_cutout)
        distance = cutout_obj.location.distance(current_cutout.location)
        if len(cutouts_sorted) == 0:
            cutouts_sorted = [current_cutout]
        elif distance < cutout_obj.location.distance(cutouts_sorted[0].location):
            cutouts_sorted.insert(0, current_cutout)
        else:
            i = 1
            while i < len(cutouts_sorted) and cutout_obj.location.distance(cutouts_sorted[i].location) < distance:
                i += 1
            if i < len(cutouts_sorted):
                cutouts_sorted.insert(i, current_cutout)
            else:
                cutouts_sorted.append(current_cutout)
    return cutouts_sorted


def get_cutout_meta(som, cutout):
    data_lut = list(csv.reader(open(som.dataset.csv_path.path), delimiter=' '))
    header = data_lut[0]
    data = data_lut[cutout.index+1]
    return dict(zip(header, data))


def create_cutout_obj(cutout_meta, som, cutout):
    ra = cutout_meta[som.dataset.obj_ra_key]
    dec = cutout_meta[som.dataset.obj_dec_key]
    cutout_loc = AladinLocation(ra, dec)
    # TODO: Not sure if on demand generation of Cutout Objects is a good idea
    identifier = "Unknown"
    if cutout_meta.keys().__contains__(som.dataset.obj_identifier_key):
        identifier = cutout_meta[som.dataset.obj_identifier_key]
    cutout_obj = CutoutObj(identifier, cutout_loc, cutout)
    return cutout_obj


class AladinLocation(cc.CcLocation):
    def __init__(self, ra, dec):
        """
        Aladin takes spherical J200 coordinates. To simplify transformations and prevent format issues,
        we wrap the AstropyCoordinate
        """
        try:
            self.coord = ac.SkyCoord(ra, dec)
        except UnitsError:
            self.coord = ac.SkyCoord(ra, dec, unit='deg')
        self.ra = self.coord.ra.hms
        self.dec = self.coord.dec.dms
        self.decD = self.dec.d
        self.decM = np.abs(self.dec.m)
        self.decS = np.abs(self.dec.s)
        self.ra_str, self.dec_str = self.coord.to_string('hmsdms').split(" ")

    def distance(self, ground):
        """
        Since we are working with spherical coordinates,
        we compute the spherical distance
        :param ground: The other location
        :return: The spherical distance in degrees
        """
        return self.coord.separation(ground.coord)

    def is_at(self, ground):
        """
        No usage so far
        """
        pass

    def is_in(self, ground):
        """
        No usage so far
        """
        pass

    def is_neighbor(self, ground):
        """
        No usage so far
        """
        pass

    def is_part(self, ground):
        """
        No usage so far
        """
        pass

    def to_dict(self):
        dictionary = {}
        dictionary['ra'] = self.ra_str
        dictionary['dec'] = self.dec_str
        return dictionary


class CutoutObj(cc.CcObject):
    def __init__(self, identifier, location, db_obj):
        """
        For current purposes, it is enough to define an object via identifier and location
        """
        self.identifier = identifier
        self.location = location
        self.db_obj = db_obj # Couple to the respective database object to spare further requests

    def bounds(self):
        return self.location

    def relation(self, obj, relType):
        """
        Currently not needed
        """
        pass

    def property(self, prop):
        if prop == 'identifier':
            return self.identifier
        elif prop == 'location':
            return self.location
        elif prop == 'db_obj':
            return self.db_obj
        elif self.location.coord_dict.__contains__(prop):
            return self.location.coord_dict[prop]
        else:
            raise ValueError("CutoutObj has no property named {0}".format(prop))

    def identity(self, obj):
        return self.db_obj.id == obj.db_obj.id

    def to_dict(self):
        dictionary = {}
        dictionary['identifier'] = self.identifier
        dictionary['location'] = self.location.to_dict()
        dictionary['db_obj'] = self.db_obj.to_json()
        return dictionary


class FoV(cc.CcGranularity):
    def __init__(self, fov, unit):
        """
        The resolution of the field of view in Aladin is given as an angle.
        We provide multiple ways to express this angle initially, but it is returned in degrees
        """
        self.fov = fov
        self.unit = unit

    def get_fov(self):
        if self.unit == 'deg':
            return self.fov
        elif self.unit == 'rad':
            return self.fov * (180/np.pi)
        elif self.unit == 'arcmin':
            return self.fov/60
        elif self.unit == 'arcsec':
            return self.fov/3600
        else:
            raise ValueError("Unknown unit:", self.unit)
