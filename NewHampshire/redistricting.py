import numpy as np
import random
import pandas as pd
import math
from osgeo import ogr
import os

print(os.getcwd())

os.chdir('./HarvardData/')

###################################################
def MH(start, steps, neighbor, goodness, moveprob):
    #  object starting state   |         |
    #         integer steps to be taken for M-H algorithm.
    #                function returning a neighbor of current state
    #                          function for determining goodness.
    #                                    function which takes goodnesses and returns probabilities.
    
    current = start.copy()
    best_state = start.copy()
    current_goodness = goodness(current)
    best_goodness = current_goodness
    better_hops = 0
    worse_hops = 0
    stays = 0
    for i in range(steps):
        possible = neighbor(current)
        possible_goodness = goodness(possible)
        if best_goodness < possible_goodness:
            best_state = possible.copy()
            best_goodness = possible_goodness
        if random.random() < moveprob(current_goodness, possible_goodness):
            if current_goodness < possible_goodness :
                better_hops += 1
            else:
                worse_hops += 1
            current = possible.copy()
            current_goodness = possible_goodness
        else:
            stays += 1
    return((best_state, best_goodness, better_hops, worse_hops, stays))

#######################################################################

def MH_swarm(starts, steps, neighbor, goodness, moveprob):
    #        As in MH, but with multiple starts
    walkers = [MH(start, steps, neighbor, goodness, moveprob) for start in starts]
    return sorted(walkers, key = lambda x: x[1], reverse = True)


#######################################################################

def neighbor(state):
    
    newstate = state.copy()
    missingdist = set.difference(set(range(ndistricts)), set(state['value']))
    #If we've blobbed out some districts, we wants to behave differently
    
    if len(missingdist) == 0:
        switchedge = random.randint(1, adjacencyFrame.shape[0]-1)
        lownode  = adjacencyFrame['low'][switchedge]
        highnode = adjacencyFrame['high'][switchedge]
        #Randomly choose an adjacency.  Find the low node and high node for that adjacency.
    
        while newstate.value[newstate.key == lownode].item() == newstate.value[newstate.key == highnode].item():
            #If the two nodes have the same district, choose a different edge.  Keep trying.
            switchedge = random.randint(1, adjacencyFrame.shape[0]-1)
            lownode  = adjacencyFrame['low'][switchedge]
            highnode = adjacencyFrame['high'][switchedge]
        
        if random.random() < 0.5:
            newstate.value[newstate.key ==  lownode] = (newstate[newstate.key == highnode].value).item()
        else:
            newstate.value[newstate.key == highnode] = (newstate[newstate.key ==  lownode].value).item()
        #We want to assign both nodes the same value, and there's a 50% chance for each value being chosen.
        
    else:
        #If there are some districts missing, 
        newstate.loc[np.random.randint(newstate.shape[0])].value = list(missingdist)[0]
        #We want to select one randomly, and make it one of the missing districts
     
    return newstate

def contiguousness(state, district):
    
    regions = 0
    regionlist = list(state.key[state.value == district])
    if len(regionlist) == 0:
        return 1
    
    subframe = adjacencyFrame[[(adjacencyFrame['low'][i] in regionlist) and (adjacencyFrame['high'][i] in regionlist) \
                               for i in range(adjacencyFrame.shape[0])]]
    subedges = subframe[subframe.length != 0][['low','high']]
    
    while len(regionlist) > 0:
        regions += 1
        currentregion = set()
        addons = {regionlist[0]}
        while len(addons) > 0:
            currentregion = currentregion.union(addons)
            subsubedges = subedges[[(subedges['low'][i] in currentregion) or (subedges['high'][i] in currentregion) \
                                    for i in subedges.index]]
            if(not subsubedges.empty):
                addons = set(subsubedges['low']).union(set(subsubedges['high'])) - currentregion
            else:
                addons = set()
        regionlist = [x for x in regionlist if x not in currentregion]
    return regions

def perimeter(state, district):
    regionlist = list(state.key[state.value == district])
    return sum(adjacencyFrame[[(adjacencyFrame['low'][i] in regionlist) != (adjacencyFrame['high'][i] in regionlist) \
                               for i in range(adjacencyFrame.shape[0])]]['length'])

def interiorPerimeter(state, district):
    regionlist = list(state.key[state.value == district])
    return sum(adjacencyFrame[[(adjacencyFrame['low'][i] in regionlist) and (adjacencyFrame['high'][i] in regionlist) \
                               for i in range(adjacencyFrame.shape[0])]]['length'])

def population(state, district):
    return sum(blockstats.population[blockstats.VTD.isin(list(state.key[state.value == district]))])

def efficiency(state, district):
    #returns difference in percentage of votes wasted.  Negative values benefit R.
    subframe = blockstats.loc[blockstats.VTD.isin(list(state.key[state.value == district]))]
    rvotes = sum(subframe['repvotes'])
    dvotes = sum(subframe['demvotes'])
    
    if rvotes > dvotes:
        wastedR = max(rvotes, dvotes) - 0.5
        wastedD = min(rvotes,dvotes)
    else:
        wastedD = max(rvotes, dvotes) - 0.5
        wastedR = min(rvotes,dvotes)
    
    return wastedR-wastedD 

def bizarreness(state, district):
    outer = perimeter(state, district)
    inner = interiorPerimeter(state, district)
    if inner + outer == 0:
        return np.nan
    return outer/(inner + outer)

def compactness1(state):
    return sum([perimeter(state, district) for district in range(ndistricts)])/2

def goodness(state):
    #Haves
        #contiguousness
        #evenness of population
        #efficiency
        #bizarreness
    #Needs
        #Compactness
    
    stconts = [contiguousness(state, i) for i in range(ndistricts)]
    stpops  = [population(state, i) for i in range(ndistricts)]
    steffic = [efficiency(state, i) for i in range(ndistricts)]
    stbiz   = [bizarreness(state, i) for i in range(ndistricts)]
    
    modTotalVar = sum([abs(float(x)/totalpopulation - float(1)/ndistricts) for x in stpops])/(2*(1-float(1)/ndistricts))
    
    #return -3000*abs(sum(stconts) - ndistricts) - 100*modTotalVar - 10*abs(sum(steffic)) -10*np.nansum(stbiz)
    return -3000*abs(sum(stconts) - ndistricts) - 100*modTotalVar -10*np.nansum(stbiz)

def switchDistrict(current_goodness, possible_goodness): # fix
    return float(1)/(1 + np.exp((current_goodness-possible_goodness)/1000.0))

def contiguousStart():
    state = pd.DataFrame([[blockstats.VTD[i], ndistricts] for i in range(0,nvtd-1)])
    state.columns = ['key', 'value']

    missingdist = set(range(ndistricts))
    while len(list(missingdist)) > 0:
        state.value[random.randint(0,nvtd-1)] = list(missingdist)[0]
        missingdist = set.difference(set(range(ndistricts)), set(state['value']))
    
    while ndistricts in set(state['value']):
        
        subframe = state.loc[state.value!=ndistricts]
        detDists = set(subframe.key)
        tbdDists = set.difference(set(state.key), detDists)
        relevantAdjacencies = adjacencyFrame.loc[(adjacencyFrame.low.isin(detDists)) != (adjacencyFrame.high.isin(detDists))]
        #adjacencies where either low or high have a value that still has value of ndistricts, but the other doesn't
        
        #choose entry in relevantAdjacencies and switch the value of the other node.
        temp = relevantAdjacencies.loc[relevantAdjacencies.index[random.randint(0,relevantAdjacencies.shape[0]-1)]]
        if temp.high in tbdDists:
            state.value[state.key == temp.high] = state.value[state.key == temp.low].item()
        else:
            state.value[state.key == temp.low] = state.value[state.key == temp.high].item()
            
    return state

###############################

#Lookup number of congressional districts state gets
cdtable = pd.read_csv('../../cdbystate1.txt', '\t')
ndistricts = int(cdtable[cdtable['STATE']=='NH'].CD)

#Lookup number of VTDs state has
ds = ogr.Open("./nh_final.shp")
nlay = ds.GetLayerCount()
lyr = ds.GetLayer(0)
nvtd = len(lyr)

#Read adjacency frame
adjacencyFrame = pd.read_csv('../HarvardData/VTDconnections.csv')
adjacencyFrame = adjacencyFrame.drop('Unnamed: 0', 1)
adjacencyFrame.columns = ['low', 'high', 'length']
adjacencyFrame.low  = [x[5:] for x in adjacencyFrame.low]
adjacencyFrame.high = [x[5:] for x in adjacencyFrame.high]

#Read blockstats
blockstats = pd.read_csv("../HarvardData/NHVTDstats.csv")
blockstats = blockstats.drop('Unnamed: 0', 1)
blockstats.set_index(blockstats.VTD)

totalpopulation = sum(blockstats.population)
