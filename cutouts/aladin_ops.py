from UltraPINK import coreconcepts as cc
import numpy as np


class AladinLocation(cc.CcLocation):
    def __init__(self, raH, raM, raS, decD, decM, decS):
        """
        Aladin takes spherical J200 coordinates. To simplify transformations and prevent format issues,
        we save each decimal individually
        """
        self.raH = raH
        self.raM = raM
        self.raS = raS
        self.decD = decD
        self.decM = decM
        self.decS = decS


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
