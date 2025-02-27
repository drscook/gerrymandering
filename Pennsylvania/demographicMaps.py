from bisect import bisect


def color_by_rgb(geom_to_plot, vtds_rgb_dict, foldername, number):
    #colors = colorDict(ndistricts)
    #colors = {0:'yellow',1:'green'}
    #ax.set_xlim([-71.8, -71.2])
    #ax.set_ylim([42.6, 43.2])
    
    subset = vtds_rgb_dict.keys()
    thing = zip(geom_to_plot['paths'], geom_to_plot['names'])
    paths = [x[0] for x in thing if x[1] in subset]
    names = [x[1] for x in thing if x[1] in subset]
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_xlim(geom_to_plot['xlim'])
    ax.set_ylim(geom_to_plot['ylim'])
    
    for p in range(len(paths)):
        path = paths[p]
        facecolor = vtds_rgb_dict[names[p]]
        patch = mpatches.PathPatch(path,facecolor=facecolor, edgecolor='black', linewidth=0.02)
        ax.add_patch(patch)
    ax.set_aspect(1.0)
    #plt.show()
    plt.savefig(foldername+'output%04d.png'%(number), dpi=2400)
    plt.clf()
    del fig

highesthisp = max(blockstats.B03002e1.values/blockstats.B02001e1.values)
loghighesthisp = np.log10(max(blockstats.B03002e1.values/blockstats.B02001e1.values))
hisp = {blockstats.VTD[i] : (1 - blockstats.B03002e1[i]/blockstats.B02001e1[i]/highesthisp, 1, 1) for i in blockstats.index}
loghisp = {blockstats.VTD[i] : (1 - max(0, np.log10(blockstats.B03002e1[i]/blockstats.B02001e1[i]))/loghighesthisp, 1, 1) for i in blockstats.index}

highestblack = max(blockstats.B02009e1.values/blockstats.B02001e1.values)
black = {blockstats.VTD[i] : (1 - (blockstats.B02009e1[i]/blockstats.B02001e1[i])/highestblack, 1 - (blockstats.B02009e1[i]/blockstats.B02001e1[i])/highestblack, 1) for i in blockstats.index}

highestincomelog = max(np.log10(blockstats.B19301e1.values))
numiles = 25
dangle = np.percentile(blockstats.B19301e1[-blockstats.B19301e1.isnull()].values, np.arange(0, 100, 100.0/numiles))
income = {blockstats.VTD[i] : (np.sqrt(1 - float(bisect(dangle, blockstats.B19301e1[i]))/numiles), np.sqrt(1 - float(bisect(dangle, blockstats.B19301e1[i]))/numiles), 1) for i in blockstats.index}

color_by_rgb(g, black, "tests/aframmap", 0)
color_by_rgb(g, hisp, "tests/hispmap", 0)
color_by_rgb(g, loghisp, "tests/loghispmap", 0)
color_by_rgb(g, income, "tests/incomemap", 1)

edgetracker = pd.DataFrame([[0]]*blockstats.shape[0])
edgetracker = edgetracker.set_index(blockstats.index)
edgetracker.columns = ['concdiff']

for i in blockstats.index:
    #look at all vtds
    #compare concentration at i with concentration at i's neighbors
    relevantAdjacencies = adjacencyFrame.ix[(adjacencyFrame.length!=0) & ((adjacencyFrame.low == i) | (adjacencyFrame.high == i)), :]
    neighbors = list(set(relevantAdjacencies.low).union(set(relevantAdjacencies.high)) - set([i]))
    iconcentration = blockstats.B02009e1[i]/blockstats.B02001e1[i]
    neighconcentrations = blockstats.B02009e1[neighbors].values/blockstats.B02001e1[neighbors].values
    
    edgetracker.ix[i,'concdiff'] = np.nanmean(np.abs(iconcentration-neighconcentrations))

highestconc = max(edgetracker.concdiff)
edgetracker.ix[:, 'concdiff'] = edgetracker.concdiff.values/highestconc

concedges = {blockstats.VTD[i] : (1 - edgetracker.concdiff[i], 1 - edgetracker.concdiff[i], 1) for i in blockstats.index}

color_by_rgb(g, concedges, "tests/communitymap", 1)

blockstats['aframcon'] = blockstats.B02009e1.values/blockstats.B02001e1.values

compoundmap = {blockstats.VTD[i] : (1 - blockstats.aframcon[i] - (min(edgetracker.concdiff[i], 0.5) if blockstats.aframcon[i] < 0.5 else 0), \
                                    1 - blockstats.aframcon[i] - (min(edgetracker.concdiff[i], 0.5) if blockstats.aframcon[i] < 0.5 else 0), \
                                    1 - edgetracker.concdiff[i]) \
               for i in blockstats.index}
color_by_rgb(g, compoundmap, "tests/communitymap", 2)

def minorityDists(conccolumn, stats = blockstats, popcolumn = 'population'):
    #contiguousstart stuff starting with highest concentration of minority of choice
    #blob stuff in until not a majority minority district.
    #repeat for remaining area.
    #return state of these regions
    
    state = pd.DataFrame({"key":stats.VTD.copy(), "value":0 })
    subAdj = adjacencyFrame.ix[adjacencyFrame.low.isin(stats.VTD) & adjacencyFrame.high.isin(stats.VTD) & (adjacencyFrame.length != 0), ['low','high']]
    subAdj.ix[:, 'lowdist']  = [0]*subAdj.shape[0]
    subAdj.ix[:, 'highdist'] = [0]*subAdj.shape[0]
    
    blobsremaining = any(stats.ix[:, conccolumn] > 0.5)
    vtdsremaining = list(stats.index)
    while blobsremaining:
        currentregion = set()
        addons = set([stats.index[stats.index.isin(vtdsremaining) & (stats.ix[:, conccolumn] > 0.5)][0]])
        
        while len(addons) > 0:
            currentregion = currentregion.union(addons)
            subedges = subAdj.loc[subAdj.low.isin(currentregion) | subAdj.high.isin(currentregion)]
            addons = set((stats.index[stats.index.isin(set(subedges.low).union(set(subedges.high))) & (stats.ix[:, conccolumn] > 0.5)])) - currentregion
        
        concentration = np.nansum(stats.ix[currentregion,conccolumn]*stats.ix[currentregion, popcolumn])/np.nansum(stats.ix[currentregion, popcolumn])
        while concentration > 0.5:
            subedges = subAdj.loc[subAdj.low.isin(currentregion) | subAdj.high.isin(currentregion)]
            neighbors = set(subedges.low).union(set(subedges.high)) - currentregion
            newvtd = stats.ix[stats.index.isin(neighbors), conccolumn].idxmax()
            currentregion = currentregion.union(set([newvtd]))
            concentration = np.nansum(stats.ix[currentregion,conccolumn]*stats.ix[currentregion, popcolumn])/np.nansum(stats.ix[currentregion, popcolumn])
            print(concentration)
        
        currentregion = currentregion - set([newvtd])
        vtdsremaining = [x for x in vtdsremaining if x not in currentregion]
        state.ix[currentregion, 'value'] = 1
        blobsremaining = any(stats.ix[vtdsremaining, conccolumn] > 0.5)
        subAdj = subAdj.ix[subAdj.low.isin(vtdsremaining) & subAdj.high.isin(vtdsremaining), :]
    
    return state

minorityblob = {i : (1 - state.value[state.key == i].item(), 1 - state.value[state.key == i].item(), 1) for i in blockstats.VTD}
color_by_rgb(g, minorityblob, 'tests/minorityblob', 1)

def isislandland(state, district):
    return [vtd for vtd in state.key[state.value == district] if (sum(adjacencyFrame.isSame[(adjacencyFrame.low == vtd) | (adjacencyFrame.high == vtd)]) == 0)]
