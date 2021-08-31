from UltraPINK import coreconcepts as cc


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