import json
import numpy as np
from aircraft import Aircraft
from vertiports import Vertiports



def schedules(filename):
    policy = dict()
    vehicles = set()
    veh_no = 0
    start_time = 21633
    with open(filename) as fp:
        for line in fp:
            line = line.split(',')
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

def tower_schedules(filename):
    schedule = []
    with open(filename) as fp:
        for i,raw_line in enumerate(fp):
            if i==0:
                line = [x.strip() for x in raw_line.split(',')]
                no_vehicles = len(line)-4
            else:
                accept = set()
                line = [int(x.strip()) for x in raw_line.split(',')]
                for l_i in line[-3:]:
                    if l_i != 0: accept.add(l_i)
                schedule.append(dict([['Requests',line[:-4]],['Avail',line[-4]],['No_requests',len(np.nonzero(line[:-4]))],['Allocate',accept]]))
    return schedule



SF_GPS = (37.773972,-122.431297)



verts = Vertiports(POV_center=SF_GPS)
verts.addPorts('Scenarios/areacre.txt')
verts.tower_clusters(10)

time_policy = []
# vehicles, policy = policies('Scenarios/policy.txt')
tower_sched = tower_schedules('Scenarios/test_medium19.csv')
allowed_ports = ['WP52','WP555','WP322','WP848']
vehicles, time_policy = schedules('Scenarios/single_tower_policy.txt')
vehicle_array = dict()
vehicle_queue = []
open_slots = list(range(8))
queue_full = False
no_active = 0
avail_slots = 0
i = 0
if time_policy:
    pass
else:
    for v_i in vehicles:
        track = verts.convertTrack(policy[v_i])
        vehicle_array[v_i] = Aircraft(loc=tuple(verts.array[policy[v_i][0][0]].loc_gps)+(100,), POV_center=SF_GPS,col=(0,1,0),ax=ax,track=track,track_col=my_palette(i))
        i+=1