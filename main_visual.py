import json
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
from ast import literal_eval
from matplotlib.animation import FuncAnimation
import numpy as np
from aircraft import Aircraft
from vertiports import Vertiports



# ---------- PART 1: Globals

n_agents = 20
my_dpi = 96
# Writer = matplotlib.animation.writers['ffmpeg']
# writer = Writer(fps=2.5, metadata=dict(artist='Me'), bitrate=1800)
fig = plt.figure(figsize=(2000/my_dpi, 1600/my_dpi), dpi=my_dpi)
img = plt.imread("mapimage.jpeg")
my_palette = plt.cm.get_cmap("Set2",n_agents)
frames = 100
ax = plt.subplot()
ax.imshow(img,extent=[-15,15,-10,10])
ax.set_xlim(-15,15)
ax.set_ylim(-10,10)
plt.hsv()
SF_GPS = (37.773972,-122.431297)
prev_time= 0


def update(i):
	global prev_time
	artist_array = []
	for v_i in vehicle_array:
		artist_array += vehicle_array[v_i].simulate(i-prev_time)
	prev_time = i
	return artist_array


def policies(filename):
	policy = dict()
	vehicles = set()
	with open(filename) as fp:
		for line in fp:
			line = line.split()
			if 'Time:' in line:
				time = int(line[1])
				policy[time] = dict()
			else:
				policy[time][line[0]] = line[1:]
				vehicles.add(line[0])
	return vehicles, policy

verts = Vertiports(POV_center=SF_GPS)
verts.addPorts('Scenarios/areacre.txt')
vehicles, policy = policies('Scenarios/policy.txt')
vehicle_array = dict()
i = 0
for v_i in vehicles:
	track = verts.convertTrack(policy[0][v_i])
	vehicle_array[v_i] = Aircraft(loc=tuple(verts.array[policy[0][v_i][0]].loc_gps)+(100,), POV_center=SF_GPS,col=(0,1,0),ax=ax,track=track,track_col=my_palette(i))
	i+=1

# vehicles = []
# vehicles.append(Aircraft(loc=(37.756800,-122.434700,100),POV_center=SF_GPS,ax=ax))
# vehicles.append(Aircraft(loc=(37.33254, -121.88718,100),POV_center=SF_GPS,ax=ax))
# art.resizeAircraft(ax,2)
# vehicles[0].moveAircraft([5,5])
# vehicles[1].updateColor((0,1,0))
# vehicle_array['kp000'].simulate(100)
ani = FuncAnimation(fig, update, frames=250, interval=200, blit=True)
plt.show(block=True)
# plt.show(block=True)



# ---------- PART 2:

