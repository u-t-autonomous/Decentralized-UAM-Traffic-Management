import math
import numpy as np
from pandas import DataFrame
from sklearn.cluster import KMeans
import matplotlib.patches as mpatches
from sklearn import metrics
import random

def depth(l):
    if isinstance(l, list):
        return 1 + max(depth(item) for item in l)
    else:
        return 0

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

    def convertTrack(self, track):
        if isinstance(track, list):
            outTrack = []
            for t_i in track:
                outTrack.append(self.array[t_i].loc_xy)
        else:
            outTrack = []
            for i in track:
                insideTrack = []
                for t_i in track[i]:
                    insideTrack.append(self.array[t_i].loc_xy)
                outTrack.append(insideTrack)
        return outTrack

    def towerClusters(self,n=10):
        towers = dict({'x':[],'y':[]})
        tower_names = []
        for t_i in self.array:
            x,y = self.array[t_i].loc_xy
            towers['x'].append(x)
            towers['y'].append(y)
            tower_names.append(self.array[t_i].name)
        df = DataFrame(towers,columns=['x','y'])
        towers['x'] = np.array(towers['x'])
        towers['y'] = np.array(towers['y'])
        kmeans = KMeans(n_clusters=n).fit(df)
        centroids = kmeans.cluster_centers_
        self.towers = []
        for i,c_i in enumerate(centroids):
            sub_names = set(np.array(tower_names)[kmeans.labels_== i])
            tower_range = max([np.linalg.norm(np.subtract(i, c_i)) for i in zip(towers['x'][kmeans.labels_ == i], towers['y'][kmeans.labels_ == i])])
            self.towers.append(Tower(self.map_center,c_i,tower_range,sub_names))
        # print(centroids)

    def plotTowers(self,ax):
        assert self.towers
        self.tower_art = []
        for t_i in self.towers:
            t_i.plotTower(ax)

    def findTower(self,wp):
        for k_i in self.towers:
            if wp in k_i.attached_vertiports:
                return (k_i.loc_xy,k_i.tower_range)
        print("No tower found")

    def findTower_ind(self,wp):
        for ind,k_i in enumerate(self.towers):
            if wp in k_i.attached_vertiports:
                return k_i

    def findPort(self,loc):
        for w_i in self.array:
            if loc == self.array[w_i].loc_xy:
                return w_i

class Vertiport(Vertiports):
    def __init__(self, POV_center, loc_gps, name):
        super(Vertiport, self).__init__(POV_center=POV_center)
        self.loc_gps = loc_gps
        self.loc_xy = super().GPS_2_coord(loc_gps)
        self.name = name

class Tower(Vertiports):
    def __init__(self, map_center, centroid, tower_range, sub_names):
        super(Tower, self).__init__(POV_center=map_center)
        self.loc_xy = tuple(centroid)
        self.loc_GPS = super().coord_2_GPS(centroid)
        self.tower_range = tower_range
        self.attached_vertiports = sub_names
        self.no_active = 0
        self.avail_slots = 3
        self.allocating_flag = False
        self.queue_full = False
        self.vehicle_array = dict()
        self.vehicle_index = dict()
        self.no_slots = 8

    def plotTower(self, ax, col=(0, 0, 1)):
        self.color = col
        art = mpatches.Circle(self.loc_xy, self.tower_range, color=self.color, fill=False, linewidth=3)
        self.tower_art = ax.add_patch(art)

    def colorTower(self, col):
        self.color = col
        self.tower_art.set_color(self.color)
        return self.tower_art

    def towerSchedules(self, filename, allowed_ports):
        schedule = []
        self.allocating_flag = True
        with open(filename) as fp:
            for i, raw_line in enumerate(fp):
                if i == 0:
                    line = [x.strip() for x in raw_line.split(',')]
                    no_vehicles = len(line) - 4
                else:
                    accept = set()
                    line = [int(x.strip()) for x in raw_line.split(',')]
                    for l_i in line[-3:]:
                        if l_i != 0: accept.add(l_i)
                    schedule.append(dict([['Requests', line[:-4]], ['Avail', line[-4]], ['No_requests', len(np.nonzero(line[:-4]))], ['Allocate', accept]]))
        self.schedule = schedule
        self.allowed_ports = allowed_ports

    def activeRequest(self):
        assert self.schedule
        self.active_request = self.schedule.pop(0)
        self.avail_slots = self.active_request['Avail']
        return self.active_request

    def clearRequest(self):
        self.active_request = None

    def requestLanded(self):
        self.no_active -= 1

    def towerUpdate(self):
        if self.allocating_flag:
            if self.avail_slots - self.no_active == 0:
                return self.colorTower((1, 0, 0))
            elif self.avail_slots - self.no_active == 1:
                return self.colorTower((1, 0.65, 0))
            elif self.avail_slots - self.no_active == 2:
                return self.colorTower((1, 1, 0))
            elif self.avail_slots - self.no_active == 3:
                return self.colorTower((0, 1, 0))

    def landWaypoint(self, ind):
        return self.allowed_ports[self.active_request['Requests'][ind - 1] - 1]

    def add_vehicle(self,veh):
        open_slots = list(range(self.no_slots))
        for k_i in self.vehicle_array:
            open_slots.remove(k_i)
        self.vehicle_array.update({random.choice(open_slots):veh})
        self.vehicle_index = {v:k for k,v in self.vehicle_array.items()}

    def remove_vehicle(self,veh):
        del_keys = []
        for r_v in self.vehicle_array:
            if veh == self.vehicle_array[r_v]:
                del_keys.append(r_v)
        for d_k in del_keys:
            del self.vehicle_array[d_k]
        self.vehicle_index = {v: k for k, v in self.vehicle_array.items()}