import math
import numpy as np
from pandas import DataFrame
from sklearn.cluster import KMeans
import matplotlib.patches as mpatches
from sklearn import metrics
import random
import sys,subprocess

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
            # self.towers.append(Tower(self.map_center,c_i,tower_range,sub_names))
            if 'WP52' in sub_names or 'WP308' in sub_names or 'WP9' in sub_names:
                self.towers.append(Scheduler(self.map_center, c_i, tower_range, sub_names, specfilename='request_handler_example.slugsin'))
            else:
                self.towers.append(Tower(self.map_center, c_i, tower_range, sub_names))
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
        self.requesting_agents = list(np.zeros(shape=(self.no_slots,),dtype=int))

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

    # def activeRequest(self):
    #     assert self.schedule
    #     self.requesting_agents = list(np.zeros(shape=(self.no_slots,), dtype=int))
    #     for v_i in self.vehicle_array:
    #         if self.vehicle_array[v_i].loitering:
    #             self.requesting_agents[v_i] = self.allowed_ports.index(self.vehicle_array[v_i].land_wp) + 1
    #     ## --- Plug in trace from synthesis here ---
    #     self.active_request = self.schedule.pop(0)
    #     self.avail_slots = 3-len(self.active_request['Allocate'])
    #     # self.avail_slots -= len(self.active_request['Allocate'])
    #     # self.active_request = None
    #     # self.avail_slots = self.active_request['Avail']
    #     return self.active_request

    def clearRequest(self):
        self.active_request = None

    def requestLanded(self):
        self.avail_slots += 1
        # self.no_active -= 1

    def towerUpdate(self):
        if self.allocating_flag:
            if self.avail_slots == 0:
                return self.colorTower((1, 0, 0))
            elif self.avail_slots == 1:
                return self.colorTower((1, 0.65, 0))
            elif self.avail_slots == 2:
                return self.colorTower((1, 1, 0))
            elif self.avail_slots == 3:
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


class Scheduler(Tower):

    def __init__(self,map_center, centroid, tower_range, sub_names,specfilename):
        super().__init__(map_center, centroid, tower_range, sub_names)

        # ==================================
        # Start slugs
        # ==================================

        # Trace element description:
        # 0: chosen by the computer
        # 1: chosen by the user
        # 2: value forced by the safety assumptions and guarantees
        # 3: value forced by the safety assumptions and guarantees and the values chosen by the user
        #
        # The types must be numbered such that taking the minimum of different values for different bits
        # (except for edited_by_hand) gives the correct labelling for a composite value obtained by merging the bits to an integer value.

        self.CHOSEN_BY_COMPUTER = 0
        self.EDITED_BY_HAND = 1
        self.FORCED_VALUE_ASSUMPTIONS = 2
        self.FORCED_VALUE_ASSUMPTIONS_AND_GUARANTEES = 3
        self.FORCED_VALUE_ASSUMPTIONS_AND_STRATEGY = 4

        argv = ['cursesSimulator.py', specfilename]
        specFile = " ".join(argv[1:])
        slugsLink = argv[0][0:argv[0].rfind("cursesSimulator.py")] + "~/slugs/src/slugs"
        self.slugsProcess = subprocess.Popen(slugsLink + " --interactiveStrategy " + specFile, shell=True, bufsize=1048000,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        # Get input APs
        self.slugsProcess.stdin.write("XPRINTINPUTS\n".encode())
        self.slugsProcess.stdin.flush()
        self.slugsProcess.stdout.readline()  # Skip the prompt
        lastLine = " "
        self.inputAPs = []
        while (lastLine != ""):
            lastLine = self.slugsProcess.stdout.readline().decode().strip()
            if lastLine != "":
                self.inputAPs.append(lastLine)

        # Get output APs
        self.slugsProcess.stdin.write("XPRINTOUTPUTS\n".encode())
        self.slugsProcess.stdin.flush()
        self.slugsProcess.stdout.readline()  # Skip the prompt
        lastLine = " "
        self.outputAPs = []
        while (lastLine != ""):
            lastLine = self.slugsProcess.stdout.readline().decode().strip()
            if lastLine != "":
                self.outputAPs.append(lastLine)



        # ==================================
        # Parse input and output bits into structured form
        # ==================================
        self.structuredVariables = []
        self.structuredVariablesBitPositions = []
        self.structuredVariablesMin = []
        self.structuredVariablesMax = []
        self.structuredVariablesIsOutput = []

        for (isOutput, source, startIndex) in [(False, self.inputAPs, 0), (True, self.outputAPs, len(self.inputAPs))]:
            # First pass: Find the limits of all integer variables
            for i, a in enumerate(source):
                if "@" in a:
                    # is Structured
                    (varName, suffix) = a.split("@")
                    if "." in suffix:
                        # Is a master variable
                        (varNum, minimum, maximum) = suffix.split(".")
                        assert varNum == "0"
                        self.structuredVariables.append(varName)
                        self.structuredVariablesBitPositions.append({0: i + startIndex})
                        self.structuredVariablesMin.append(int(minimum))
                        self.structuredVariablesMax.append(int(maximum))
                        self.structuredVariablesIsOutput.append(isOutput)

            # Second pass: parse all other variables
            for i, a in enumerate(source):
                if "@" in a:
                    (varName, suffix) = a.split("@")
                    if not "." in suffix:
                        # Is a slave variable
                        indexFound = False
                        for j, b in enumerate(self.structuredVariables):
                            if b == varName:
                                indexFound = j
                        if indexFound == None:
                            print(sys.stderr, "Error in input instance: Master variables have to occur before the slave variables in the input file.\n")
                            sys.exit(1)
                        assert self.structuredVariablesIsOutput[indexFound] == isOutput
                        self.structuredVariablesBitPositions[indexFound][int(suffix)] = i + startIndex
                else:
                    # is Unstructured
                    self.structuredVariables.append(a)
                    self.structuredVariablesBitPositions.append({0: i + startIndex})
                    self.structuredVariablesMin.append(0)
                    self.structuredVariablesMax.append(1)
                    self.structuredVariablesIsOutput.append(isOutput)



        maxLenInputOrOutputName = 15  # Minimium size
        for a in self.structuredVariables:
            maxLenInputOrOutputName = max(maxLenInputOrOutputName, len(a))
        if len(self.structuredVariables) == 0:
            print(sys.stderr, "Error: No variables found. Cannot run simulator.\n")
            sys.exit(1)

        self.unfixedState = []
        for i in range(0, len(self.structuredVariables)):
            self.unfixedState.append((self.structuredVariablesMin[i], self.CHOSEN_BY_COMPUTER))
        self.unfixedState = tuple(self.unfixedState)  # Enforce non-mutability for the rest of this script
        self.trace = [list(self.unfixedState)]
        self.traceGoalNumbers = [(0, 0)]
        self.traceFlags = [set([])]
        self.initializeTrace()

    def computeBinarySlugsStringFromStructuredLabeledTraceElementsForcedElements(self,traceElement):
        result = {}
        for i, name in enumerate(self.structuredVariables):
            (chosenValue, assignmentType) = traceElement[i]
            encodedValue = chosenValue - self.structuredVariablesMin[i]
            for (a, b) in self.structuredVariablesBitPositions[i].items():
                if assignmentType != self.EDITED_BY_HAND:
                    result[b] = '.'
                elif (encodedValue & (1 << a)) > 0:
                    result[b] = '1'
                else:
                    result[b] = '0'
        result = "".join([result[a] for a in range(0, len(result))])
        return result

    def computeBinarySlugsStringFromStructuredLabeledTraceElementsAllElements(self,traceElement):
        result = {}
        for i, name in enumerate(self.structuredVariables):
            (chosenValue, assignmentType) = traceElement[i]
            encodedValue = chosenValue - self.structuredVariablesMin[i]
            for (a, b) in self.structuredVariablesBitPositions[i].items():
                if (encodedValue & (1 << a)) > 0:
                    result[b] = '1'
                else:
                    result[b] = '0'
        result = "".join([result[a] for a in range(0, len(result))])
        return result

    def parseBinaryStateTupleIntoStructuredTuple(self,structuredTuple):
        result = []
        for i, name in enumerate(self.structuredVariables):
            thisOne = self.structuredVariablesMin[i]
            types = set([])
            for (a, b) in self.structuredVariablesBitPositions[i].items():
                # print >>sys.stderr,(a,b)
                # print >>sys.stderr,(structuredTuple)
                if structuredTuple[b] == "A":
                    thisOne += 1 << a
                    types.add(self.FORCED_VALUE_ASSUMPTIONS)
                elif structuredTuple[b] == "a":
                    types.add(self.FORCED_VALUE_ASSUMPTIONS)
                elif structuredTuple[b] == "G":
                    thisOne += 1 << a
                    types.add(self.FORCED_VALUE_ASSUMPTIONS_AND_GUARANTEES)
                elif structuredTuple[b] == "g":
                    types.add(self.FORCED_VALUE_ASSUMPTIONS_AND_GUARANTEES)
                elif structuredTuple[b] == "S":
                    thisOne += 1 << a
                    types.add(self.FORCED_VALUE_ASSUMPTIONS_AND_STRATEGY)
                elif structuredTuple[b] == "s":
                    types.add(self.FORCED_VALUE_ASSUMPTIONS_AND_STRATEGY)
                elif structuredTuple[b] == "1":
                    thisOne += 1 << a
                    types.add(self.CHOSEN_BY_COMPUTER)
                elif structuredTuple[b] == "0":
                    types.add(self.CHOSEN_BY_COMPUTER)
                else:
                    print(sys.stderr, "Error: Found literal ", structuredTuple[b], " in structured Tuple")
                    assert False
            result.append((thisOne, min(types)))
        return result

    def initializeTrace(self):
        # ==================================
        # Initialize CURSES
        # ==================================
        # ==================================
        # Main loop
        # ==================================
        postTrace = []  # When going back to earlier trace elements, forced entries in later trace elements are stored
        # Update initial state whenever we can
        if not "(OOB)" in self.traceFlags[0]:
            writtenElement = self.computeBinarySlugsStringFromStructuredLabeledTraceElementsForcedElements(
                self.trace[0])
            self.slugsProcess.stdin.write(("XCOMPLETEINIT\n" + writtenElement).encode())
            self.slugsProcess.stdin.flush()
            self.slugsProcess.stdout.readline()  # Skip the prompt
            initLine = self.slugsProcess.stdout.readline().decode().strip()
            isValidElement = True
            if (initLine == "FAILASSUMPTIONS"):
                self.traceFlags[0].add("A")
                isValidElement = False
            else:
                if "A" in self.traceFlags[0]:
                    self.traceFlags[0].remove("A")
            if (initLine == "FAILGUARANTEES"):
                self.traceFlags[0].add("G")
                isValidElement = False
                # Read a new line
                initLine = self.slugsProcess.stdout.readline().decode().strip()
            else:
                if "G" in self.traceFlags[0]:
                    self.traceFlags[0].remove("G")
            if (initLine == "FORCEDNONWINNING"):
                self.traceFlags[0].add("L")
                isValidElement = False
            else:
                if "L" in self.traceFlags[0]:
                    self.traceFlags[0].remove("L")

            if isValidElement:
                parsedTraceElement = self.parseBinaryStateTupleIntoStructuredTuple(initLine)
                # Merge the computed concretized trace element back into the actual trace
                for i in range(0, len(self.structuredVariables)):
                    if self.trace[0][i][1] == self.EDITED_BY_HAND:
                        assert self.trace[0][i][0] == parsedTraceElement[i][0]
                    else:
                        self.trace[0][i] = parsedTraceElement[i]
        self.trace.append(list(self.unfixedState))
        self.traceFlags.append(set([]))
        self.traceGoalNumbers.append((0, 0))

    def updateTrace(self):

        if not "(OOB)" in self.traceFlags[len(self.trace) - 1]:
            currentElement = self.computeBinarySlugsStringFromStructuredLabeledTraceElementsAllElements(
                self.trace[len(self.trace) - 2])
            successorElement = self.computeBinarySlugsStringFromStructuredLabeledTraceElementsForcedElements(
                self.trace[len(self.trace) - 1])
            dataForStrategyTransition = currentElement + successorElement + "\n" + str(
                self.traceGoalNumbers[len(self.trace) - 2][0]) + "\n" + str(self.traceGoalNumbers[len(self.trace) - 2][1])
            self.slugsProcess.stdin.write(("XSTRATEGYTRANSITION\n" + dataForStrategyTransition + "\n").encode())
            self.slugsProcess.stdin.flush()
            self.slugsProcess.stdout.readline().decode()  # Skip the prompt
            positionLine = self.slugsProcess.stdout.readline().decode().strip()
            isValidElement = True
            if (positionLine == "FAILASSUMPTIONS"):
                self.traceFlags[len(self.trace) - 1].add("A")
                isValidElement = False
            else:
                if "A" in self.traceFlags[len(self.trace) - 1]:
                    self.traceFlags[len(self.trace) - 1].remove("A")
            if (positionLine == "FAILGUARANTEES"):
                self.traceFlags[len(self.trace) - 1].add("G")
                isValidElement = True
                # Read a new line
                positionLine = self.slugsProcess.stdout.readline().decode().strip()
            else:
                if "G" in self.traceFlags[len(self.trace) - 1]:
                    self.traceFlags[len(self.trace) - 1].remove("G")
            if (positionLine == "FORCEDNONWINNING"):
                self.traceFlags[len(self.trace) - 1].add("L")
                isValidElement = False
            else:
                if "L" in self.traceFlags[len(self.trace) - 1]:
                    self.traceFlags[len(self.trace) - 1].remove("L")

            if isValidElement:
                parsedTraceElement = self.parseBinaryStateTupleIntoStructuredTuple(positionLine)
                # Merge the computed concretized trace element back into the actual trace
                for i in range(0, len(self.structuredVariables)):
                    if self.trace[len(self.trace) - 1][i][1] == self.EDITED_BY_HAND:
                        if self.trace[len(self.trace) - 1][i][0] != parsedTraceElement[i][0]:
                            asdf = 1
                        assert self.trace[len(self.trace) - 1][i][0] == parsedTraceElement[i][0]
                    else:
                        self.trace[len(self.trace) - 1][i] = parsedTraceElement[i]

                nextLivenessAssumption = int(self.slugsProcess.stdout.readline().decode().strip())
                nextLivenessGuarantee = int(self.slugsProcess.stdout.readline().decode().strip())
                self.traceGoalNumbers[len(self.trace) - 1] = (nextLivenessAssumption, nextLivenessGuarantee)



    def inputTrace(self):
        self.updateTrace()
        if any(self.trace[len(self.trace) - 1][x][1] == self.CHOSEN_BY_COMPUTER for x in range(9)):
            for ind, element in enumerate(self.trace[len(self.trace) - 1]):
                if element[1] == self.CHOSEN_BY_COMPUTER and ind < 8:
                    inp = self.requesting_agents[ind]
                    self.trace[len(self.trace) - 1][ind] = (inp, self.EDITED_BY_HAND)

                elif element[1] == self.CHOSEN_BY_COMPUTER and ind == 8:
                    inp = self.avail_slots
                    self.trace[len(self.trace) - 1][ind] = (inp, self.EDITED_BY_HAND)

    def outputTrace(self):
        return set([x[0] for x in self.trace[-2][9:12]])

    def activeRequest(self):
        # assert self.schedule
        self.requesting_agents = list(np.zeros(shape=(self.no_slots,), dtype=int))
        for v_i in self.vehicle_array:
            if self.vehicle_array[v_i].loitering:
                self.requesting_agents[v_i] = self.allowed_ports.index(self.vehicle_array[v_i].land_wp) + 1
        self.inputTrace()
        self.updateTrace()
        print(self.trace[-1])
        self.trace.append(list(self.unfixedState))
        self.traceFlags.append(set([]))
        self.traceGoalNumbers.append((0, 0))
        ## --- Plug in trace from synthesis here ---
        # self.active_request = self.schedule.pop(0)
        self.active_request = dict([['Allocate',[]],['Requests',self.requesting_agents]])
        self.active_request['Allocate'] = self.outputTrace()
        self.active_request['Allocate'].discard(0)
        if len(self.active_request['Allocate'])>0:
            print('Allocating aircraft: {}'.format(self.active_request['Allocate']))
        # self.avail_slots = 3-len(self.active_request['Allocate'])
        self.avail_slots -= len(self.active_request['Allocate'])
        # self.active_request = None
        # self.avail_slots = self.active_request['Avail']
        return self.active_request
