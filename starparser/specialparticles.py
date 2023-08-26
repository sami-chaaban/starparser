import numpy as np
import pandas as pd
import sys

"""
--extract_if_nearby
"""
def findnearby(coreparticles,nearparticles,threshdist):

    """
    coreparticles comes from --i and nearparticles comes from --f
    Workflow: go micrograph by micrograph and find the nearest distance to
    particles in the second file, then compare that to the threshold requested
    """

    #It makes this easier later if we remove the path to the micrograph name
    #(i.e. everything before the last '/'). This name is stored in a new column
    coreparticles["_rlnMicrographNameSimple"] = coreparticles['_rlnMicrographName'].str.split('/').str[-1]
    nearparticles["_rlnMicrographName"] = nearparticles["_rlnMicrographName"].str.split('/').str[-1]

    #Create a grouby object that is grouped by micrographs
    coremicrographs = coreparticles.groupby(["_rlnMicrographNameSimple"])

    #get_loc finds the index of the column for retrieval later down the function
    #(Consider simplifying this such that the columns are called directly.)
    coremicloc = coreparticles.columns.get_loc("_rlnMicrographName")+1
    corexloc = coreparticles.columns.get_loc("_rlnCoordinateX")+1
    coreyloc = coreparticles.columns.get_loc("_rlnCoordinateY")+1
    corenameloc = coreparticles.columns.get_loc("_rlnImageName")+1
    
    #Do the same for the second star file
    nearmicrographs = nearparticles.groupby(["_rlnMicrographName"])
    nearxloc = nearparticles.columns.get_loc("_rlnCoordinateX")+1
    nearyloc = nearparticles.columns.get_loc("_rlnCoordinateY")+1

    #Initialize a list that will store particles that do not have a neighbor
    #in the second star file (i.e the second file lacks particles in that micrograph)
    noparts=[]

    #This will store the particles that are too far
    farparts=[]

    #This will store all the nearest distances for plotting later
    alldistances=[]

    #Iterate through the micrographs from the first star file
    for coremicrograph in coremicrographs:
        
        #To check if there are particles in the second star file for this micrograph,
        #we will try to get_group that micrograph, if it fails, there are none
        try:
            nearmicrograph = nearmicrographs.get_group(coremicrograph[0])

        #It is bad practice to have a naked exception here. Works for now. Consider revising.
        except:

            #If there are no particles in the second file, store all the particles from 
            #the first file in the noparts list.
            for coreparticle in coremicrograph[1].itertuples():
                noparts.append(coreparticle[corenameloc])

            #Continue allows us to exit this iteration of the for loop
            #and continue to the next micrograph
            continue 
        
        #Now that we have the particles from the same micrograph, we can calculate
        #nearest distances, one particle at a time.
        for coreparticle in coremicrograph[1].itertuples():

            """
            Our goal is to calculate the distance between the current particle and all particles
            from the second file, allowing us to find the one that has the smallest distance
            """

            #Get the x and y coordinate for this particle. They come in as strings
            #so we have to convert them to float
            x1 = float(coreparticle[corexloc])
            y1 = float(coreparticle[coreyloc])
            
            #We will store the x,y coordinates of all particles in the second
            #star file in this list
            nearparticlelocs=[]

            #This one-liner (1) loops through particles in the second star file (2) turns the
            #x,y coordinates into floats and (3) adds it to the nearparticlelocs list
            #(i.e. [[x2,y2], [x3,y3], etc.])
            [nearparticlelocs.append([float(n[nearxloc]),float(n[nearyloc])]) for n in nearmicrograph.itertuples()]

            """
            Instead of calculating one-by-one the distance between the x1,y1 and 
            each coordinate in the second micrograph, we can turn the list into an
            array and use numpy to apply the distance equation to the whole array
            """
            #Turn it into an array
            nearparticlelocs = np.asarray(nearparticlelocs)
            #calculate the distances in one go
            distances = np.sqrt(np.sum((nearparticlelocs - [x1,y1])**2, axis=1))

            #Find the minimum from the array of distances
            mindistance = np.min(distances)

            #Store the nearest distance in alldistances
            alldistances.append(mindistance)

            #If the nearest distance is further than the requested threshold,
            #it goes in the farparts list
            if mindistance > threshdist:
                farparts.append(coreparticle[corenameloc])


    """
    We now have a list of particles whose nearest neighbor is too far (farparts)
    and a list of particles that don't have a corresponding neighbor (noparts)
    """

    """
    With dataframes, stating dataframe1 = dataframe2 only creates
    a reference. Therefore, we must create a copy if we want to leave
    the original dataframe unmodified.
    """
    farparticles = coreparticles.copy()

    #We can use pandas to only keep particles that are in the farparts list
    farparticles = farparticles[farparticles['_rlnImageName'].isin(farparts)]

    #The same thing for the close particles
    closeparticles = coreparticles.copy()

    #but in this case, we want the opposite (hence the tilde ~)
    closeparticles = closeparticles[~closeparticles['_rlnImageName'].isin(farparts)]

    #Particles that didn't have a corresponding neighbor should be removed from
    #both dataframes since they are neither far nor close.
    if len(noparts) != 0:
        farparticles = farparticles[~farparticles['_rlnImageName'].isin(noparts)]
        closeparticles = closeparticles[~closeparticles['_rlnImageName'].isin(noparts)]

    print("\n>> Out of " + str(len(coreparticles.index)) + ", the subsets have:\n-FAR: " + str(len(farparticles.index)) + " particles\n-CLOSE: " + str(len(closeparticles.index)) + " particles\n-NO-MATCH: " + str(len(noparts)) + " particles\n")

    #We can remove the new column we made above before returning the dataframes
    closeparticles.drop("_rlnMicrographNameSimple", axis=1, inplace=True)
    farparticles.drop("_rlnMicrographNameSimple", axis=1, inplace=True)

    return(farparticles, closeparticles, alldistances)

"""
--fetch_from_nearby
"""
def fetchnearby(coreparticles,nearparticles,threshdist,columnstoretrieve):

    #Create a grouby object that is grouped by micrographs
    coremicrographs = coreparticles.groupby(["_rlnMicrographName"])

    #get_loc finds the index of the column for retrieval later down the function
    #(Consider simplifying this such that the columns are called directly.)
    coremicloc = coreparticles.columns.get_loc("_rlnMicrographName")+1
    corexloc = coreparticles.columns.get_loc("_rlnCoordinateX")+1
    coreyloc = coreparticles.columns.get_loc("_rlnCoordinateY")+1
    corenameloc = coreparticles.columns.get_loc("_rlnImageName")+1

    #Do the same for the second star file
    nearmicrographs = nearparticles.groupby(["_rlnMicrographName"])
    nearxloc = nearparticles.columns.get_loc("_rlnCoordinateX")+1
    nearyloc = nearparticles.columns.get_loc("_rlnCoordinateY")+1

    #Initialize a list that will store particles that do not have a neighbor
    #in the second star file (i.e the second file lacks particles in that micrograph)
    noparts=[]

    #This will store the particles that are too far
    farparts=[]

    #We'll initialize a dataframe that's identical to the original one
    #that we will modify in the loop below
    """
    With dataframes, stating dataframe1 = dataframe2 only creates
    a reference. Therefore, we must create a copy if we want to leave
    the original dataframe unmodified.
    """
    stolenparticles = coreparticles.copy()

    #Loop through the micrographs
    for coremicrograph in coremicrographs:

        #To check if there are particles in the second star file for this micrograph,
        #we will try to get_group that micrograph, if it fails, there are none
        try:
            nearmicrograph = nearmicrographs.get_group(coremicrograph[0])

        #It is bad practice to have a naked exception here. Works for now. Consider revising.
        except:

            #If there are no particles in the second file, store all the particles from 
            #the first file in the noparts list.
            for coreparticle in coremicrograph[1].itertuples():
                noparts.append(coreparticle[corenameloc])

            #Continue allows us to exit this iteration of the for loop
            #and continue to the next micrograph
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

    print("\n>> " + str(len(stolenparticles.index)) + " out of " + str(len(coreparticles.index)) + " (" + str(round(100*(len(stolenparticles.index)/len(coreparticles.index)),1)) + "%) " + "had neighbors close enough to fetch from. " + str(len(farparts)) + " were too far and " + str(len(noparts)) + " did not have neighbors.")

    return(stolenparticles)

"""
--extract_clusters
"""
def getcluster(particles,threshold,minimum):

    #~needs explanation~#

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
        print(">> Error: all particles were retained. No star file will be output.\n")
        sys.exit()

    """
    With dataframes, stating dataframe1 = dataframe2 only creates
    a reference. Therefore, we must create a copy if we want to leave
    the original dataframe unmodified.
    """
    particles_purged = particles.copy()

    toconcat = [particles_purged[particles_purged["_rlnImageName"] == q] for q in keep]

    particles_purged = pd.concat(toconcat)

    return(particles_purged)

"""
--extract_minimum
"""
def extractwithmin(particles,minimum):

    #~needs explanation~#

    uniquemics = particles.groupby(["_rlnMicrographName"])
    nameloc = particles.columns.get_loc("_rlnImageName")+1

    keep = []
    badmics = 0
    for mic in uniquemics:
        if len(mic[1]) > minimum:
            for particle in mic[1].itertuples():
                keep.append(particle[nameloc])
        else:
            badmics+=1

    if len(keep) == 0:
        print("\n>> Error: no particles were retained based on the criteria.\n")
        sys.exit()
    elif len(keep) == len(particles.index):
        print("\n>> Error: all particles were retained. No star file will be output.")
        sys.exit()

    print(">> " + str(badmics) + " micrographs don't meet the criteria.\n")

    """
    With dataframes, stating dataframe1 = dataframe2 only creates
    a reference. Therefore, we must create a copy if we want to leave
    the original dataframe unmodified.
    """
    particles_purged = particles.copy()

    toconcat = [particles_purged[particles_purged["_rlnImageName"] == q] for q in keep]

    particles_purged = pd.concat(toconcat)

    return(particles_purged)