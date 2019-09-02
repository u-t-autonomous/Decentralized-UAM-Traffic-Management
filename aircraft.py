import math
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.collections as collections
import matplotlib.transforms as transforms
import numpy as np

class UpdateablePatchCollection(collections.PatchCollection):
    def __init__(self,patches,*args,**kwargs):
        self.patches = patches
        collections.PatchCollection.__init__(self, patches, *args, **kwargs)

    def get_paths(self):
        self.set_paths(self.patches)
        return self._paths

# class Track():
#     def __init__(self):
#

class Aircraft():

    def __init__(self,loc=(0,0,0),col=(0,0,0),track=None,POV_center=(0,0),ax=None,speed=0.05,track_col=(1,1,1),launch_time=0):
        self.map_center = POV_center
        self.scale = [1.0/1287500,1.0/462102]
        self.axis = ax
        self.loc_gps = loc # GPS co-ordinates (lat,lon,alt)
        self.loc = self.GPS_2_coord(loc) # x,y,z coordinates w.r.t to map center
        self.col = col
        self.speed = speed
        self.world_time = launch_time
        self.drone_art = self.add_aircraft()
        self.moveAircraft([self.loc[0],self.loc[1]])
        self.updateColor(self.col)
        self.track_plotting = True
        if track:
            self.add_track(track, track_col)

    def GPS_2_coord(self,loc_gps):
        earth_rad = 6.371e6
        x = earth_rad*(loc_gps[1]-self.map_center[1])*math.cos(self.map_center[0])
        y = earth_rad*(loc_gps[0]-self.map_center[0])
        return x*self.scale[0],y*self.scale[1],loc_gps[2]

    def coord_2_GPS(self,xyz):
        earth_rad = 6.371e6
        lon = xyz[0]/(earth_rad*math.cos(self.map_center[0]))+self.map_center[1]
        lat = xyz[1]/earth_rad + self.map_center[0]
        return lat,lon,xyz[2]

    def add_track(self,track,track_col):
        self.track = []
        self.track_times = []
        self.track_col = track_col
        time_lapse = 0
        for t_i in track:
            idx = track.index(t_i)
            if idx ==0:
                self.track_times.append(time_lapse)
            else:
                distance = np.array(t_i) - np.array(track[idx - 1])
                time_lapse += np.linalg.norm(distance)/self.speed
                self.track_times.append(time_lapse)
            self.track.append(t_i)
        if self.track_plotting:
            x_points, y_points = map(list, zip(*self.track))
            l_i, = self.axis.plot(x_points, y_points, color=self.track_col, alpha=0.6, linewidth=3)
            self.track_plot = l_i

    def update_track(self):
        assert self.track
        artist_array = []
        if self.track_plotting:
            x_points, y_points = map(list, zip(*self.track))
            self.track_plot.set_data(x_points,y_points)
            artist_array.append(self.track_plot)
        return artist_array

    def updateColor(self,c):
        artists_array = [self.aircraft_artists[0]]
        self.col = c
        self.aircraft_artists[0].set_color(c)
        for a_i in self.aircraft_artists[1:]:
            a_i.set_color(c)
            artists_array.append(a_i)
        return artists_array

    def simulate(self,time):
        track_x,track_y = map(list,zip(*self.track))
        near_path_x = track_x[0:2]
        near_path_y = track_y[0:2]
        path_angle = np.arctan2(near_path_y[1]-near_path_y[0],near_path_x[1]-near_path_x[0])
        dxdy = [self.speed*time*np.cos(path_angle), self.speed*time*np.sin(path_angle)]
        out_art = self.moveAircraft(dxdy)
        self.loc = (self.loc[0]+dxdy[0], self.loc[1]+dxdy[1], self.loc[2])
        self.loc_gps = self.coord_2_GPS(self.loc)
        if self.world_time < self.track_times[1]:
            self.track[0] = [self.loc[0],self.loc[1]]
        else:
            self.track.pop(0)
            self.track_times.pop(0)
            if len(self.track)<2:
                self.track.append(self.track[0])
                self.track_times.append(self.track_times[0])
                self.speed = 0
                out_art += self.updateColor((1,0,0))
            else:
                out_art += self.updateColor((1,0.6,0))
        self.world_time += time
        if self.track_plotting:
            out_art += self.update_track()
        return out_art


    def add_aircraft(self):
        drone_circles = [
        mpatches.Wedge([0, 0], 0.08,0,360,width=0.002),
        mpatches.Wedge([0.26, 0.26], 0.24,0,360,width=0.002),
        mpatches.Wedge([-0.26, -0.26], 0.24,0,360,width=0.002),
        mpatches.Wedge([0.26, -0.26], 0.24,0,360,width=0.002),
        mpatches.Wedge([-0.26, 0.26], 0.24,0,360,width=0.002),
        mpatches.Wedge([0.26, 0.26], 0.21,0,360,width=0.002),
        mpatches.Wedge([-0.26, -0.26], 0.21,0,360,width=0.002),
        mpatches.Wedge([0.26, -0.26], 0.21,0,360,width=0.002),
        mpatches.Wedge([-0.26, 0.26], 0.21,0,360,width=0.002),
        mpatches.Wedge([0.26, 0.26], 0.25,0,360,width=0.002),
        mpatches.Wedge([-0.26, -0.26], 0.25,0,360,width=0.002),
        mpatches.Wedge([0.26, -0.26], 0.25,0,360,width=0.002),
        mpatches.Wedge([-0.26, 0.26], 0.25,0,360,width=0.002),
        mpatches.Wedge([0.26, 0.26], 0.025,0,360,width=0.002),
        mpatches.Wedge([-0.26, -0.26], 0.025,0,360,width=0.002),
        mpatches.Wedge([0.26, -0.26], 0.025,0,360,width=0.002),
        mpatches.Wedge([-0.26, 0.26], 0.025,0,360,width=0.002)]

        drone_verts = [
            [[-0.01, 0.27], [0, 0.26]],
            [[-0.01, 0.25], [0, 0.26]],
            [[-0.01, 0.01], [0.0, 0.0]],
            [[0.01, -0.25], [0, 0.26]],
            [[0.01, -0.27], [0, 0.26]],
            [[0.01, -0.01], [0.0, 0.0]],
            [[-0.01, 0.25], [0, -0.26]],
            [[-0.01, 0.27], [0, -0.26]],
            [[-0.01, 0.01], [0.0, 0.0]],
            [[0.01, -0.25], [0, -0.26]],
            [[0.01, -0.27], [0, -0.26]],
            [[0.01, -0.01], [0.0, 0.0]]
        ]
        drone_lines = []
        for d_v in drone_verts:
            l, = self.axis.plot(d_v[0],d_v[1],color=self.col,linewidth=2,linestyle='solid')
            drone_lines.append(l)
        drone_patch = UpdateablePatchCollection(drone_circles,edgecolors=self.col,facecolors=self.col)
        self.axis.add_collection(drone_patch)
        self.aircraft_artists = [drone_patch]+drone_lines
        return self.aircraft_artists

    # def resizeAircraft(self,ax,scalefactor):
    #     t = ax.transData
    #     # t = ax.collections[0].get_transform()
    #     t += transforms.Affine2D().scale(scalefactor)
    #     self.aircraft_artists[0].set_transform(t)
    #     ax.add_collection(self.aircraft_artists[0])
    #     for a_i in self.aircraft_artists[1:]:
    #         t = a_i.get_transform()
    #         t += transforms.Affine2D().scale(scalefactor)
    #         a_i.set_transform(t)

    def moveAircraft(self,dxdy):
        dxdy = np.array(dxdy)
        artist_array = [self.aircraft_artists[0]]
        for a_i in self.aircraft_artists[0].patches:
            a_i.set_center(a_i.center + dxdy)
        for a_i in self.aircraft_artists[1:]:
            d_i = np.array(a_i.get_data())
            d_i[0] += dxdy[0]
            d_i[1] += dxdy[1]
            a_i.set_data(d_i)
            artist_array.append(a_i)
        return artist_array