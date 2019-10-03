#!/usr/bin/python
#
# Interactive Strategy Simulator and Debugger for Slugs
import curses, sys, subprocess
import numpy as np
import csv

def computeTrace(filename,inputdata):
    # ==================================
    # Constants
    # ==================================
    # Max size of any number in a run. Used to limit the column width
    MAX_OVERALL_NUMBER = 999999

    # Trace element description:
    # 0: chosen by the computer
    # 1: chosen by the user
    # 2: value forced by the safety assumptions and guarantees
    # 3: value forced by the safety assumptions and guarantees and the values chosen by the user
    #
    # The types must be numbered such that taking the minimum of different values for different bits (except for edited_by_hand) gives the correct labelling for a composite value obtained by merging the bits to an integer value.
    CHOSEN_BY_COMPUTER = 0
    EDITED_BY_HAND = 1
    FORCED_VALUE_ASSUMPTIONS = 2
    FORCED_VALUE_ASSUMPTIONS_AND_GUARANTEES = 3
    FORCED_VALUE_ASSUMPTIONS_AND_STRATEGY = 4


    # ==================================
    # Check parameters
    # ==================================
    if len(sys.argv)<2:
        sys.argv = ['cursesSimulator.py', 'request_handler_example.slugsin']
        # print >>sys.stderr, "Error: Need Slugsin file as parameter. Additional parameters are optional"
        # sys.exit(1)
    specFile = " ".join(sys.argv[1:])


    # ==================================
    # Start slugs
    # ==================================
    slugsLink = sys.argv[0][0:sys.argv[0].rfind("cursesSimulator.py")]+"/Users/suda/Documents/slugs/src/slugs"
    slugsProcess = subprocess.Popen(slugsLink+" --interactiveStrategy "+specFile, shell=True, bufsize=1048000, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    # Get input APs
    slugsProcess.stdin.write("XPRINTINPUTS\n")
    slugsProcess.stdin.flush()
    slugsProcess.stdout.readline() # Skip the prompt
    lastLine = " "
    inputAPs = []
    while (lastLine!=""):
        lastLine = slugsProcess.stdout.readline().strip()
        if lastLine!="":
            inputAPs.append(lastLine)

    # Get output APs
    slugsProcess.stdin.write("XPRINTOUTPUTS\n")
    slugsProcess.stdin.flush()
    slugsProcess.stdout.readline() # Skip the prompt
    lastLine = " "
    outputAPs = []
    while (lastLine!=""):
        lastLine = slugsProcess.stdout.readline().strip()
        if lastLine!="":
            outputAPs.append(lastLine)



    # ==================================
    # Parse input and output bits into structured form
    # ==================================
    structuredVariables = []
    structuredVariablesBitPositions = []
    structuredVariablesMin = []
    structuredVariablesMax = []
    structuredVariablesIsOutput = []

    for (isOutput,source,startIndex) in [(False,inputAPs,0),(True,outputAPs,len(inputAPs))]:
        # First pass: Find the limits of all integer variables
        for i,a in enumerate(source):
            if "@" in a:
                # is Structured
                (varName,suffix) = a.split("@")
                if "." in suffix:
                    # Is a master variable
                    (varNum,minimum,maximum) = suffix.split(".")
                    assert varNum=="0"
                    structuredVariables.append(varName)
                    structuredVariablesBitPositions.append({0:i+startIndex})
                    structuredVariablesMin.append(int(minimum))
                    structuredVariablesMax.append(int(maximum))
                    structuredVariablesIsOutput.append(isOutput)

        # Second pass: parse all other variables
        for i,a in enumerate(source):
            if "@" in a:
                (varName,suffix) = a.split("@")
                if not "." in suffix:
                    # Is a slave variable
                    indexFound = False
                    for j,b in enumerate(structuredVariables):
                        if b==varName:
                            indexFound=j
                    if indexFound==None:
                        print >>sys.stderr,"Error in input instance: Master variables have to occur before the slave variables in the input file.\n"
                        sys.exit(1)
                    assert structuredVariablesIsOutput[indexFound]==isOutput
                    structuredVariablesBitPositions[indexFound][int(suffix)] = i+startIndex
            else:
                # is Unstructured
                structuredVariables.append(a)
                structuredVariablesBitPositions.append({0:i+startIndex})
                structuredVariablesMin.append(0)
                structuredVariablesMax.append(1)
                structuredVariablesIsOutput.append(isOutput)


    # ===============================================
    # Translating between structured positions/states
    # and the state/position representations that
    # slugs needs
    # ===============================================
    def computeBinarySlugsStringFromStructuredLabeledTraceElementsForcedElements(traceElement):
        result = {}
        for i,name in enumerate(structuredVariables):
            (chosenValue,assignmentType) = traceElement[i]
            encodedValue = chosenValue-structuredVariablesMin[i]
            for (a,b) in structuredVariablesBitPositions[i].iteritems():
                if assignmentType!=EDITED_BY_HAND:
                    result[b] = '.'
                elif (encodedValue & (1 << a))>0:
                    result[b] = '1'
                else:
                    result[b] = '0'
        result = "".join([result[a] for a in xrange(0,len(result))])
        return result

    def computeBinarySlugsStringFromStructuredLabeledTraceElementsAllElements(traceElement):
        result = {}
        for i,name in enumerate(structuredVariables):
            (chosenValue,assignmentType) = traceElement[i]
            encodedValue = chosenValue-structuredVariablesMin[i]
            for (a,b) in structuredVariablesBitPositions[i].iteritems():
                if (encodedValue & (1 << a))>0:
                    result[b] = '1'
                else:
                    result[b] = '0'
        result = "".join([result[a] for a in xrange(0,len(result))])
        return result


    def parseBinaryStateTupleIntoStructuredTuple(structuredTuple):
        result = []
        for i,name in enumerate(structuredVariables):
            thisOne = structuredVariablesMin[i]
            types = set([])
            for (a,b) in structuredVariablesBitPositions[i].iteritems():
                # print >>sys.stderr,(a,b)
                # print >>sys.stderr,(structuredTuple)
                if structuredTuple[b]=="A":
                    thisOne += 1 << a
                    types.add(FORCED_VALUE_ASSUMPTIONS)
                elif structuredTuple[b]=="a":
                    types.add(FORCED_VALUE_ASSUMPTIONS)
                elif structuredTuple[b]=="G":
                    thisOne += 1 << a
                    types.add(FORCED_VALUE_ASSUMPTIONS_AND_GUARANTEES)
                elif structuredTuple[b]=="g":
                    types.add(FORCED_VALUE_ASSUMPTIONS_AND_GUARANTEES)
                elif structuredTuple[b]=="S":
                    thisOne += 1 << a
                    types.add(FORCED_VALUE_ASSUMPTIONS_AND_STRATEGY)
                elif structuredTuple[b]=="s":
                    types.add(FORCED_VALUE_ASSUMPTIONS_AND_STRATEGY)
                elif structuredTuple[b]=="1":
                    thisOne += 1 << a
                    types.add(CHOSEN_BY_COMPUTER)
                elif structuredTuple[b]=="0":
                    types.add(CHOSEN_BY_COMPUTER)
                else:
                    print >>sys.stderr, "Error: Found literal ",structuredTuple[b]," in structured Tuple"
                    assert False
            result.append((thisOne,min(types)))
        return result

    # ==================================
    # Prepare visualization
    # ==================================
    # print "Out:",structuredVariables
    # print "Out:",structuredVariablesBitPositions
    # print "Out:",structuredVariablesMin
    # print "Out:",structuredVariablesMax
    # print "Out:",structuredVariablesIsOutput
    #
    # print "inputAPs:",inputAPs
    # print "outputAPs:",outputAPs

    maxLenInputOrOutputName = 15 # Minimium size
    for a in structuredVariables:
        maxLenInputOrOutputName = max(maxLenInputOrOutputName,len(a))
    if len(structuredVariables)==0:
        print >>sys.stderr, "Error: No variables found. Cannot run simulator.\n"
        sys.exit(1)


    # ==================================
    # Get initial state
    # ==================================
    # slugsProcess.stdin.write("XGETINIT\n")
    # slugsProcess.stdin.flush()
    # slugsProcess.stdout.readline() # Skip the prompt
    # initLine = slugsProcess.stdout.readline().strip()
    # currentState = parseBinaryStateTupleIntoStructuredTuple(initLine)


    # ==================================
    # Initialize Trace
    # ==================================
    unfixedState = []
    for i in xrange(0,len(structuredVariables)):
        unfixedState.append((structuredVariablesMin[i],CHOSEN_BY_COMPUTER))
    unfixedState = tuple(unfixedState) # Enforce non-mutability for the rest of this script
    trace = [list(unfixedState)]
    # trace = [[(2,1),(2,1),(2,1),(2,1),(2,1),(2,1),(2,1),(0,0),(0,0)]]
    traceGoalNumbers = [(0,0)]
    traceFlags = [set([])]


    # ==================================
    # Initialize CURSES
    # ==================================
    try:

        # ==================================
        # Main loop
        # ==================================
        postTrace = [] # When going back to earlier trace elements, forced entries in later trace elements are stored

        while 1:

            # ==============================
            # Update Trace
            # ==============================
            if len(trace)==1:
                # Update initial state whenever we can
                if not "(OOB)" in traceFlags[0]:
                    writtenElement = computeBinarySlugsStringFromStructuredLabeledTraceElementsForcedElements(trace[0])
                    slugsProcess.stdin.write("XCOMPLETEINIT\n" + writtenElement)
                    slugsProcess.stdin.flush()
                    slugsProcess.stdout.readline()  # Skip the prompt
                    initLine = slugsProcess.stdout.readline().strip()
                    isValidElement = True
                    if (initLine=="FAILASSUMPTIONS"):
                        traceFlags[0].add("A")
                        isValidElement = False
                    else:
                        if "A" in traceFlags[0]:
                            traceFlags[0].remove("A")
                    if (initLine=="FAILGUARANTEES"):
                        traceFlags[0].add("G")
                        isValidElement = False
                        # Read a new line
                        initLine = slugsProcess.stdout.readline().strip()
                    else:
                        if "G" in traceFlags[0]:
                            traceFlags[0].remove("G")
                    if (initLine=="FORCEDNONWINNING"):
                        traceFlags[0].add("L")
                        isValidElement = False
                    else:
                        if "L" in traceFlags[0]:
                            traceFlags[0].remove("L")

                    if isValidElement:
                        parsedTraceElement = parseBinaryStateTupleIntoStructuredTuple(initLine)
                        # Merge the computed concretized trace element back into the actual trace
                        for i in xrange(0,len(structuredVariables)):
                            if trace[0][i][1]==EDITED_BY_HAND:
                                assert trace[0][i][0]==parsedTraceElement[i][0]
                            else:
                                trace[0][i] = parsedTraceElement[i]

            else:
                # Update non-initial state
                if not "(OOB)" in traceFlags[len(trace)-1]:
                    currentElement = computeBinarySlugsStringFromStructuredLabeledTraceElementsAllElements(trace[len(trace)-2])
                    successorElement = computeBinarySlugsStringFromStructuredLabeledTraceElementsForcedElements(trace[len(trace)-1])
                    dataForStrategyTransition = currentElement+successorElement+"\n"+str(traceGoalNumbers[len(trace)-2][0])+"\n"+str(traceGoalNumbers[len(trace)-2][1])
                    slugsProcess.stdin.write("XSTRATEGYTRANSITION\n" + dataForStrategyTransition + "\n")
                    slugsProcess.stdin.flush()
                    slugsProcess.stdout.readline()  # Skip the prompt
                    positionLine = slugsProcess.stdout.readline().strip()
                    isValidElement = True
                    if (positionLine=="FAILASSUMPTIONS"):
                        traceFlags[len(trace)-1].add("A")
                        isValidElement = False
                    else:
                        if "A" in traceFlags[len(trace)-1]:
                            traceFlags[len(trace)-1].remove("A")
                    if (positionLine=="FAILGUARANTEES"):
                        traceFlags[len(trace)-1].add("G")
                        isValidElement = True
                        # Read a new line
                        positionLine = slugsProcess.stdout.readline().strip()
                    else:
                        if "G" in traceFlags[len(trace)-1]:
                            traceFlags[len(trace)-1].remove("G")
                    if (positionLine=="FORCEDNONWINNING"):
                        traceFlags[len(trace)-1].add("L")
                        isValidElement = False
                    else:
                        if "L" in traceFlags[len(trace)-1]:
                            traceFlags[len(trace)-1].remove("L")

                    if isValidElement:
                        parsedTraceElement = parseBinaryStateTupleIntoStructuredTuple(positionLine)
                        # Merge the computed concretized trace element back into the actual trace
                        for i in xrange(0,len(structuredVariables)):
                            if trace[len(trace)-1][i][1]==EDITED_BY_HAND:
                                assert trace[len(trace)-1][i][0]==parsedTraceElement[i][0]
                            else:
                                trace[len(trace)-1][i] = parsedTraceElement[i]

                        nextLivenessAssumption = int(slugsProcess.stdout.readline().strip())
                        nextLivenessGuarantee = int(slugsProcess.stdout.readline().strip())
                        traceGoalNumbers[len(trace)-1] = (nextLivenessAssumption,nextLivenessGuarantee)


            # ==============================
            # Draw interface
            # ==============================

            # Paint border

            # Main part

            #=======================
            # Process key presses
            #=======================

            # 0. Truncate all currently edited numbers to their limits when moving the cursor
            if any(trace[len(trace) - 1][x][1] ==CHOSEN_BY_COMPUTER for x in range(9)):
                for ind,element in enumerate(trace[len(trace)-1]):
                    if element[1] == CHOSEN_BY_COMPUTER and ind < 8:
                        inp = inputdata[len(trace) - 1][0][ind]
                        trace[len(trace) - 1][ind] = (inp, EDITED_BY_HAND)

                    elif element[1] == CHOSEN_BY_COMPUTER and ind == 8:
                        if trace[len(trace) - 2][ind][0] > 0 and any([x[0] for x in trace[len(trace)-2][0:7]])>0 \
                                and any([x[0] for x in trace[len(trace)-2][9:12]])>0:
                            inp = 0
                        elif trace[len(trace) - 2][ind][0] > 0 or len(trace)==1:
                            inp = 1
                        else:
                            inp = np.random.choice(range(4), 1, p=[0.99, 0.01, 0.0,0])[0]
                        trace[len(trace) - 1][ind] = (inp, EDITED_BY_HAND)
            # elif len(trace) < 2:
            #     trace.append(list(unfixedState))
            #     traceFlags.append(set([]))
            #     traceGoalNumbers.append((0, 0))
            elif trace[(len(trace))-1] == trace[(len(trace))-2]:
                trace.append(list(unfixedState))
                traceFlags.append(set([]))
                traceGoalNumbers.append((0, 0))
            else:
                trace.append(list(unfixedState))
                traceFlags.append(set([]))
                traceGoalNumbers.append((0, 0))
            if len(trace) == len(inputdata)-1:
                print(trace)
                break


    # =====================
    # Cleanup Curses
    # =====================
    finally:
        # print(len(trace))
        # print((trace))
        with open(filename+'.csv', 'wb') as test_file:
            num_inputs = 7
            file_writer = csv.writer(test_file)
            for state in trace:
                file_writer.writerow([x[0] for x in state])

