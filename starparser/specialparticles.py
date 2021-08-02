import numpy as np
import pandas as pd
import sys

def findnearby(coreparticles,nearparticles,threshdist):

    coreparticles["_rlnMicrographNameSimple"] = coreparticles['_rlnMicrographName'].str.split('/').str[-1]
    nearparticles["_rlnMicrographName"] = nearparticles["_rlnMicrographName"].str.split('/').str[-1]

    coremicrographs = coreparticles.groupby(["_rlnMicrographNameSimple"])
    coremicloc = coreparticles.columns.get_loc("_rlnMicrographName")+1
    corexloc = coreparticles.columns.get_loc("_rlnCoordinateX")+1
    coreyloc = coreparticles.columns.get_loc("_rlnCoordinateY")+1
    corenameloc = coreparticles.columns.get_loc("_rlnImageName")+1
    
    nearmicrographs = nearparticles.groupby(["_rlnMicrographName"])
    nearxloc = nearparticles.columns.get_loc("_rlnCoordinateX")+1
    nearyloc = nearparticles.columns.get_loc("_rlnCoordinateY")+1

    noparts=[]
    farparts=[]
    alldistances=[]

    for coremicrograph in coremicrographs:
        
        try:
            nearmicrograph = nearmicrographs.get_group(coremicrograph[0])
        except:
            for coreparticle in coremicrograph[1].itertuples():
                noparts.append(coreparticle[corenameloc])
            continue 
        
        for coreparticle in coremicrograph[1].itertuples():
            x1 = float(coreparticle[corexloc])
            y1 = float(coreparticle[coreyloc])
            
            nearparticlelocs=[]
            [nearparticlelocs.append([float(n[nearxloc]),float(n[nearyloc])]) for n in nearmicrograph.itertuples()]
            nearparticlelocs = np.asarray(nearparticlelocs)
            distances = np.sqrt(np.sum((nearparticlelocs - [x1,y1])**2, axis=1))

            mindistance = np.min(distances)
            alldistances.append(mindistance)

            if mindistance > threshdist:
                farparts.append(coreparticle[corenameloc])

    farparticles = coreparticles.copy()
    farparticles = farparticles[farparticles['_rlnImageName'].isin(farparts)]

    closeparticles = coreparticles.copy()
    closeparticles = closeparticles[~closeparticles['_rlnImageName'].isin(farparts)]

    if len(noparts) != 0:
        farparticles = farparticles[~farparticles['_rlnImageName'].isin(noparts)]
        closeparticles = closeparticles[~closeparticles['_rlnImageName'].isin(noparts)]

    print("\n>> Out of " + str(len(coreparticles.index)) + ", the subsets have:\n-FAR: " + str(len(farparticles.index)) + " particles\n-CLOSE: " + str(len(closeparticles.index)) + " particles\n-NO-MATCH: " + str(len(noparts)) + " particles\n")

    closeparticles.drop("_rlnMicrographNameSimple", 1, inplace=True)
    farparticles.drop("_rlnMicrographNameSimple", 1, inplace=True)

    return(farparticles, closeparticles, alldistances)

def fetchnearby(coreparticles,nearparticles,threshdist,columnstoretrieve):

    coremicrographs = coreparticles.groupby(["_rlnMicrographName"])
    coremicloc = coreparticles.columns.get_loc("_rlnMicrographName")+1
    corexloc = coreparticles.columns.get_loc("_rlnCoordinateX")+1
    coreyloc = coreparticles.columns.get_loc("_rlnCoordinateY")+1
    corenameloc = coreparticles.columns.get_loc("_rlnImageName")+1

    nearmicrographs = nearparticles.groupby(["_rlnMicrographName"])
    nearxloc = nearparticles.columns.get_loc("_rlnCoordinateX")+1
    nearyloc = nearparticles.columns.get_loc("_rlnCoordinateY")+1

    noparts=[]
    farparts=[]

    stolenparticles = coreparticles.copy()

    for coremicrograph in coremicrographs:
        
        try:
            nearmicrograph = nearmicrographs.get_group(coremicrograph[0])
        except:
            for coreparticle in coremicrograph[1].itertuples():
                noparts.append(coreparticle[corenameloc])
            continue 
        
        for coreparticle in coremicrograph[1].itertuples():
            x1 = float(coreparticle[corexloc])
            y1 = float(coreparticle[coreyloc])
            nearparticlelocs=[]
            [nearparticlelocs.append([float(n[nearxloc]),float(n[nearyloc])]) for n in nearmicrograph.itertuples()]
            nearparticlelocs = np.asarray(nearparticlelocs)
            distances = np.sqrt(np.sum((nearparticlelocs - [x1,y1])**2, axis=1))
            mindistance = np.min(distances)

            if mindistance > threshdist:
                farparts.append(coreparticle[corenameloc])
            else:
                nearestid = np.argmin(distances)
                for c in columnstoretrieve:
                    nearcoldata = nearmicrograph.iloc[nearestid][c]
                    stolenparticles.iloc[coreparticle[0]][c] = nearcoldata

    stolenparticles = stolenparticles[~stolenparticles['_rlnImageName'].isin(farparts)]
    if len(noparts) != 0:
        stolenparticles = stolenparticles[~stolenparticles['_rlnImageName'].isin(noparts)]

    print(">> " + str(len(stolenparticles.index)) + " out of " + str(len(coreparticles.index)) + " (" + str(round(100*(len(stolenparticles.index)/len(coreparticles.index)),1)) + "%) " + "had neighbors close enough to fetch from. " + str(len(farparts)) + " were too far and " + str(len(noparts)) + " did not have neighbors.")

    return(stolenparticles)


def getcluster(particles,threshold,minimum):

    uniquemics = particles.groupby(["_rlnMicrographName"])
    xloc = particles.columns.get_loc("_rlnCoordinateX")+1
    yloc = particles.columns.get_loc("_rlnCoordinateY")+1
    nameloc = particles.columns.get_loc("_rlnImageName")+1

    keep = []
    for mic in uniquemics:
        coords = []
        names = []
        for particle in mic[1].itertuples():
            x = float(particle[xloc])
            y = float(particle[yloc])
            coords.append([x,y])
            names.append(particle[nameloc])
        coords = np.asarray(coords)
        for i in range(0,len(coords)):
            distances = np.sqrt(np.sum((coords - [coords[i]])**2, axis=1))
            distances = distances[np.logical_and(distances <= threshold, distances > 0)]
            if len(distances) >= minimum:
                keep.append(names[i])

    if len(keep) == 0:
        print(">> Error: no particles were retained based on the criteria.\n")
        sys.exit()
    elif len(keep) == len(particles.index):
        print(">> Error: all particles were retained. No star file will be output.")
        sys.exit()
    particles_purged = particles.copy()
    toconcat = [particles_purged[particles_purged["_rlnImageName"] == q] for q in keep]
    particles_purged = pd.concat(toconcat)

    print(">> Removed " + str(len(particles.index)-len(particles_purged.index)) + " that did not match the criteria (" + str(len(particles_purged.index)) + " remaining out of " + str(len(particles.index)) + ").")

    return(particles_purged)