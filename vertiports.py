import math
import numpy as np

class Vertiports():
    def __init__(self, POV_center=(0,0)):
        self.map_center = POV_center
        self.scale = [1.0 / 1287500, 1.0 / 462102]

    def addPorts(self,filename):
        self.array = dict()
        with open(filename) as fp:
            for line in fp:
                line = line.split()
                self.array[line[-1]] = Vertiport(self.map_center, np.array(line[0:2],dtype=float), line[-1])

    def GPS_2_coord(self,loc_gps):
        earth_rad = 6.371e6
        x = earth_rad*(loc_gps[1]-self.map_center[1])*math.cos(self.map_center[0])
        y = earth_rad*(loc_gps[0]-self.map_center[0])
        return x*self.scale[0],y*self.scale[1]

    def coord_2_GPS(self, xy):
        earth_rad = 6.371e6
        lon = xy[0]/(earth_rad*math.cos(self.map_center[0]))+self.map_center[1]
        lat = xy[1]/earth_rad + self.map_center[0]
        return lat, lon

    def convertTrack(self,track):
        outTrack = []
        for t_i in track:
            outTrack.append(self.array[t_i].loc_xy)
        return outTrack

class Vertiport(Vertiports):
    def __init__(self, POV_center, loc_gps, name):
        super(Vertiport, self).__init__(POV_center=POV_center)
        self.loc_gps = loc_gps
        self.loc_xy = super().GPS_2_coord(loc_gps)
        self.name = name