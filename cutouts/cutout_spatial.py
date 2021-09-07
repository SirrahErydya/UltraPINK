from UltraPINK import coreconcepts as cc
import numpy as np
from som import models
import csv


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
    cutout_loc = AladinLocation(cutout_meta['RaH'], cutout_meta['RaM'], cutout_meta['RaS'],
                                cutout_meta['DecD'], cutout_meta['DecM'], cutout_meta['DecS'])
    # TODO: Not sure if on demand generation of Cutout Objects is a good idea
    identifier = "Unknown"
    if cutout_meta.keys().__contains__(som.dataset.obj_identifier_key):
        identifier = cutout_meta[som.dataset.obj_identifier_key]
    cutout_obj = CutoutObj(identifier, cutout_loc, cutout)
    return cutout_obj


class AladinLocation(cc.CcLocation):
    def __init__(self, raH, raM, raS, decD, decM, decS):
        """
        Aladin takes spherical J200 coordinates. To simplify transformations and prevent format issues,
        we save each decimal individually
        """
        self.raH = float(raH)
        self.raM = float(raM)
        self.raS = float(raS)
        self.decD = float(decD)
        self.decM = float(decM)
        self.decS = float(decS)

    def distance(self, ground):
        """
        Since we are working with spherical coordinates,
        we compute the spherical distance
        :param ground: The other location
        :return: The spherical distance in degrees
        """
        l_ra = self.raH * (np.pi/12) + self.raM * (np.pi/720) + self.raS * (np.pi/43200)
        l_dec = self.decD * (np.pi/180) + self.decM * (np.pi/10800) + self.decS * (np.pi/648000)
        g_ra = ground.raH * (np.pi/12) + ground.raM * (np.pi/720) + ground.raS * (np.pi/43200)
        g_dec = ground.decD * (np.pi / 180) + ground.decM * (np.pi / 10800) + ground.decS * (np.pi / 648000)
        return np.arccos(np.sin(l_dec) * np.sin(g_dec) + np.cos(l_dec) * np.cos(g_dec) * np.cos(l_ra-g_ra)) * (180./np.pi)

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
        dictionary['raH'] = self.raH
        dictionary['raM'] = self.raM
        dictionary['raS'] = self.raS
        dictionary['decD'] = self.decD
        dictionary['decD'] = self.decM
        dictionary['decD'] = self.decS
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
