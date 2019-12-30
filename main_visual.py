import json
import matplotlib
# matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
from ast import literal_eval
from matplotlib.animation import FuncAnimation
import numpy as np
from aircraft import Aircraft
from vertiports import Vertiports
import random
random.seed(4)


# ---------- PART 1: Globals
# plt.rcParams['savefig.bbox'] = 'tight'
n_agents = 20
my_dpi = 96
Writer = matplotlib.animation.writers['ffmpeg']
writer = Writer(fps=24, metadata=dict(artist='Me'), bitrate=1800)
fig = plt.figure(figsize=(2000/my_dpi, 1600/my_dpi), dpi=my_dpi,frameon=False)
fig.set_tight_layout('True')
img = plt.imread("mapimage.jpeg")
my_palette = plt.cm.get_cmap("tab10",n_agents)
frames = 100
ax = plt.subplot()
ax.imshow(img,extent=[-15,15,-10,10])
ax.set_xlim(-15,15)
ax.set_ylim(-10,10)
# ax.axis('tight')
ax.axis('off')
plt.hsv()
SF_GPS = (37.773972,-122.431297)
prev_time= 0
j = 0


def update(i):
    global prev_time, j, vehicle_queue, verts
    dt = 0.2
    print(i)
    # loiter_dict = dict([[verts.findTower_ind(allowed_ports[2]), set()], [verts.findTower_ind(second_tower[2]), set()]])
    land_s = False
    # print(open_slots)
    if time_policy:
        t_i = i*dt
        if time_policy.get(t_i):
            # Usable cache of 8 aircraft
            for v_i in time_policy[t_i]:
                if len(verts.findTower_ind(time_policy[t_i][v_i][-1]).vehicle_array) < 8:
                    track = verts.convertTrack(time_policy[t_i][v_i])
                    vehicle_array.append(Aircraft(loc=tuple(verts.array[time_policy[t_i][v_i][0]].loc_gps)+(100,),POV_center=SF_GPS,col=(0,1,0),ax=ax,track=track,track_col=my_palette(j),land_tower=verts.findTower(time_policy[t_i][v_i][-1]),land_wp=time_policy[t_i][v_i][-1],verts=verts))
                    if len(vehicle_array[-1].scheduler_ind)> 0:vehicle_array[-1].loiter()
                    for s_k in vehicle_array[-1].scheduler_ind:
                        verts.towers[s_k].add_vehicle(vehicle_array[-1])
                    j += 1
                else:
                    track = verts.convertTrack(time_policy[t_i][v_i])
                    vehicle_queue.append((v_i,tuple(verts.array[time_policy[t_i][v_i][0]].loc_gps)+(100,),track,verts.findTower(time_policy[t_i][v_i][-1]),time_policy[t_i][v_i][-1],time_policy[t_i][v_i][-1]))
        else:
            for v_i,v_q in enumerate(vehicle_queue):
                if len(verts.findTower_ind(v_q[5]).vehicle_array) < 8:
                    v_q = vehicle_queue.pop(v_i)
                    vehicle_array.append(Aircraft(loc=v_q[1],POV_center=SF_GPS,col=(0,1,0),ax=ax,track=v_q[2],track_col=my_palette(j),land_tower=v_q[3],land_wp=v_q[4],verts=verts))
                    if len(vehicle_array[-1].scheduler_ind) > 0: vehicle_array[-1].loiter()
                    for s_k in vehicle_array[-1].scheduler_ind:
                        verts.towers[s_k].add_vehicle(vehicle_array[-1])
                    j += 1

    artist_array = []
    landed_drones = []
    for t_a in verts.towers:
        if t_a.allocating_flag:
            # if t_i.avail_slots > 0:
            t_a.queue_full = True
            t_a.activeRequest()
            # print("Avail Slots: {}".format(t_a.avail_slots))

            # t_i.clearRequest()


    land_signals = dict([[v_i,None] for v_i in vehicle_array])

    ## Allocate pass-throughs/landings
    for t_ind,t_a in enumerate(verts.towers):
        for ind,v_ind in enumerate(t_a.vehicle_array):
            v_i = t_a.vehicle_array[v_ind]
            if t_a.active_request:
                if v_ind+1 in t_a.active_request['Allocate']:
                    v_i.pass_flag[t_ind] = True
                    # land_s = verts.array[v_i.land_wp].loc_xy # verts.array[t_i.landWaypoint(ind)].loc_xy ## TODO fix with pass-throughs
                    # print(land_s)
                    # land_signals[v_i] = land_s

    for v_i in vehicle_array:
        artist_array += v_i.simulate(dt, land_signal=land_signals[v_i])
        if v_i.kill:
            landed_drones.append(v_i)

    # Remove landing drones
    for v_i in landed_drones:
        for t_a in v_i.scheduler_ind:
            if v_i in verts.towers[t_a].vehicle_array.values():
                verts.towers[t_a].remove_vehicle(v_i)
                verts.towers[t_a].requestLanded()
        vehicle_array.remove(v_i)

    ## Add vehicles to towers if not in
    for v_i in vehicle_array:
        for t_a in v_i.scheduler_ind:
            if v_i not in verts.towers[t_a].vehicle_array.values():
                verts.towers[t_a].add_vehicle(v_i)

    for t_ind,t_a in enumerate(verts.towers):
        pass_vehicles = []
        for v_i in t_a.vehicle_array:
            if verts.insideTower(t_a.vehicle_array[v_i].loc[0:2])[t_ind] == 0:
                pass_vehicles.append(t_a.vehicle_array[v_i])
        for v_i in pass_vehicles:
            t_a.remove_vehicle(v_i)
            t_a.requestLanded()


    for t_a in verts.towers:
        out_art = t_a.towerUpdate()
        if out_art: artist_array.append(out_art)
    # f = open('loiter_log.txt',"a")
    # f.write(str(i) + "|\t")
    # for l_i in loiter_dict:
        # f.write(str(loiter_dict[l_i])+", "+str(l_i.avail_slots)+", "+str(l_i.no_active)+"|\t")
    # f.write("\n")
    prev_time = i

    return artist_array

def schedules(filename):
    policy = dict()
    vehicles = set()
    veh_no = 0
    start_time = 21633
    with open(filename) as fp:
        for line in fp:
            line = line.split(',')
            if line[2] not in allowed_ports+second_tower+third_tower:
                line[2] = random.choice(allowed_ports+second_tower+third_tower)
            policy[int(float(line[0]))-start_time] = dict({veh_no:line[1:3]})
            vehicles.add(veh_no)
            veh_no += 1
    return vehicles, policy


def policies(filename):
    policy = dict()
    vehicles = set()
    with open(filename) as fp:
        for line in fp:
            line = line.split()
            if 'Time:' in line:
                time = int(line[1])
            else:
                if policy.get(line[0]):
                    policy[line[0]][time] = line[1:]
                else:
                    policy[line[0]] = dict()
                    policy[line[0]][time] = line[1:]
                vehicles.add(line[0])
    return vehicles, policy


no_towers = 2
verts = Vertiports(POV_center=SF_GPS)
verts.addPorts('Scenarios/areacre.txt')
# f = open('loiter_log.txt',"w")
verts.towerClusters(10)
verts.plotTowers(ax)
time_policy = []
# vehicles, policy = policies('Scenarios/policy.txt')
allowed_ports = ['WP52','WP555','WP322']
second_tower = ['WP802','WP989','WP778']
third_tower = ['WP94','WP661','WP9']
verts.findTower_ind(allowed_ports[2]).towerSchedules('Scenarios/test_medium19.csv',allowed_ports)
verts.findTower_ind(second_tower[2]).towerSchedules('Scenarios/test_medium40_csv.csv',second_tower)
verts.findTower_ind(third_tower[2]).towerSchedules('Scenarios/test_medium40_csv.csv',third_tower)

vehicles, time_policy = schedules('Scenarios/scn_UAM_testNewVT.trp')
vehicle_array = []
vehicle_queue = []
i = 0
if time_policy:
    pass
else:
    for v_i in vehicles:
        track = verts.convertTrack(policy[v_i])
        vehicle_array[v_i] = Aircraft(loc=tuple(verts.array[policy[v_i][0][0]].loc_gps)+(100,), POV_center=SF_GPS,col=(0,1,0),ax=ax,track=track,track_col=my_palette(i),verts=verts)
        i+=1
#
# for i in range(500):
#     update(i)


ani = FuncAnimation(fig, update, frames=500, interval=0.04, blit=True,repeat=False)
# ani = FuncAnimation(fig, update, frames=1000,repeat=False)
ani.save('Pass_through_allocation_decen.mp4',writer = writer)
# plt.show(block=True)
# plt.show(block=True)