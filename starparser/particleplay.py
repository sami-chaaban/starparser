import sys
import pandas as pd
import numpy as np
from starparser import argparser
from starparser import columnplay
from starparser import fileparser

import matplotlib.pyplot as plt
from matplotlib.widgets import LassoSelector
from matplotlib.path import Path
import matplotlib.patches as patches

import warnings
from matplotlib.cbook import MatplotlibDeprecationWarning
warnings.filterwarnings("ignore", category=MatplotlibDeprecationWarning)

"""
These functions still require explanations.
"""

"""
--limit
"""
def limitparticles(particles, column, limit, operator):
    
    tempcolumnname = column + "_float"
    particles[tempcolumnname] = particles[column]
    try:
        particles[tempcolumnname] = pd.to_numeric(particles[tempcolumnname], downcast="float")
    except ValueError:
        print("\n>> Error: this column doesn't seem to contain numbers.\n")
        sys.exit()
    limitedparticles = particles.copy()

    if operator == "lt":
        limitedparticles = limitedparticles[limitedparticles[tempcolumnname]<limit]
    elif operator == "gt":
        limitedparticles = limitedparticles[limitedparticles[tempcolumnname]>limit]
    elif operator == "ge":
        limitedparticles = limitedparticles[limitedparticles[tempcolumnname]>=limit]
    elif operator == "le":
        limitedparticles = limitedparticles[limitedparticles[tempcolumnname]<=limit]

    particles.drop(tempcolumnname, axis=1, inplace=True)
    limitedparticles.drop(tempcolumnname, axis=1, inplace=True)

    if len(limitedparticles.index) == 0:
        print("\n>> Error: there are no particles that match the criterion.\n")
        sys.exit()
    
    return(limitedparticles)

"""
--remove_particles
"""
def delparticles(particles, columns, query, queryexact):
    
    purgedparticles = particles.copy()
    
    if len(columns)>1:
        print("\n>> Error: you have specified two columns. You can't if you're querying to delete.\n")
        sys.exit()

    itisnumeric = True
    try:
        pd.to_numeric(particles[columns[0]], downcast="float")
    except ValueError:
        itisnumeric = False

    if not queryexact and itisnumeric:
        print("\n----------------------------------------------------------------------")        
        print("\n>> Warning: it looks like this column has numbers but you haven't specified the exact option (--e).\n   Make sure that this is the behavior you intended.\n")
        print("----------------------------------------------------------------------")

    if not queryexact:
        q = "|".join(query)
        purgedparticles.drop(purgedparticles[purgedparticles[columns[0]].str.contains(q)].index , axis=0,inplace=True)
    else:
        for q in query:
            purgedparticles.drop(purgedparticles[purgedparticles[columns[0]]==q].index , axis=0,inplace=True)
    
    return(purgedparticles)

"""
--remove_duplicates
"""
def delduplicates(particles, column):

    return(particles.drop_duplicates(subset=[column]))

"""
--remove_mics_list
"""
def delmics(particles, micstodelete):
    purgedparticles = particles.copy()
    m = "|".join(micstodelete)
    purgedparticles.drop(purgedparticles[purgedparticles["_rlnMicrographName"].str.contains(m)].index , axis=0,inplace=True)    
    return(purgedparticles)

"""
--keep_mics_list
"""
def keepmics(particles, micstokeep):
    keptparticles = particles.copy()
    m = "|".join(micstokeep)
    keptparticles = keptparticles[keptparticles["_rlnMicrographName"].str.contains(m)]
    return(keptparticles)

"""
--extract
"""
def extractparticles(particles, columns, query, queryexact):
    
    if len(columns)>1:
        print("\n>> Error: you have specified two columns. Only specify one if you're extracting from a subset of the data using a query.\n")
        sys.exit()

    itisnumeric = True
    try:
        pd.to_numeric(particles[columns[0]], downcast="float")
    except ValueError:
        itisnumeric = False

    params = argparser.argparse()

    if not queryexact and itisnumeric and not params["parser_splitoptics"] and not params["parser_classproportion"]:
        print("\n----------------------------------------------------------------------")        
        print("\n>> Warning: it looks like this column has numbers but you haven't specified the exact option (--e).\n   Make sure that this is the behavior you intended.\n")
        print("----------------------------------------------------------------------")

    if not queryexact:
        extractedparticles = particles.copy()
        q = "|".join(query)
        extractedparticles.drop(extractedparticles[~extractedparticles[columns[0]].str.contains(q)].index, axis=0,inplace=True)
    else:
        toconcat = [particles[particles[columns[0]] == q] for q in query]
        extractedparticles = pd.concat(toconcat)

    extractednumber = len(extractedparticles.index)
    
    return(extractedparticles, extractednumber)

def checksubset(particles, queryexact):
    
    """
    Re-processing the columns/queries is inefficient since it was
    already processed in decision tree. This also makes it so that
    you can't use checksubset in scripts. Consider revising.
    """

    params = argparser.argparse()
    if params["parser_column"] != "" and params["parser_query"] != "":

        query = params["parser_query"]
        escape = ",/"
        query = str.replace(params["parser_query"],escape, ",")
        query = query.split("/")
        for i,q in enumerate(query):
            query[i] = str.replace(q,",", "/")

        columns = params["parser_column"].split("/")
        for i,c in enumerate(columns):
            columns[i] = makefullname(c)
        
        subsetparticles, extractednumber = extractparticles(particles, columns, query, queryexact)
        
        print("\n>> Created a subset of " + str(extractednumber) + " particles (out of " + str(len(particles.index)) + ", " + str(round(extractednumber*100/len(particles.index),1)) + "%) that match " + str(query) +               " in the columns " + str(columns) + ".")
        
        return(subsetparticles)
    
    else:
        return(particles)

def countqueryparticles(particles,columns,query,queryexact,quiet):

    totalparticles = len(particles.index)
    
    totalquery = 0
    
    if len(columns)>1:
        print("\n>> Error: you have specified two different columns.\n")
        sys.exit()

    itisnumeric = True
    try:
        pd.to_numeric(particles[columns[0]], downcast="float")
    except ValueError:
        itisnumeric = False

    if not queryexact and itisnumeric:
        print("\n----------------------------------------------------------------------")        
        print("\n>> Warning: it looks like this column has numbers but you haven't specified the \"exact\" option (--e, see documentation).\n   Make sure that this is the behavior you intended.\n")
        print("----------------------------------------------------------------------")

    if not queryexact:
        q = "|".join(query)
        totalquery += len(particles[particles[columns[0]].str.contains(q)].index)
    else:
        for q in query:
            totalquery += len(particles[particles[columns[0]]==q].index)
        
    percentparticles = round(totalquery*100/totalparticles,1)

    if not quiet:
        print('\n>> There are ' + str(totalquery) + ' particles that match ' + str(query) + ' in the specified columns (out of ' + str(totalparticles) + ', or ' + str(percentparticles) + '%).\n')

    return(totalquery)

"""
--regroup
"""
def regroup(particles, numpergroup):
    
    newgroups = []
    roundtotal = int(len(particles.index)/numpergroup)
    leftover = (len(particles.index)) - roundtotal*numpergroup
    for i in range(roundtotal):
        newgroups.append([i+1 for j in range(numpergroup)])
    newgroups.append([newgroups[-1][-1] for i in range(leftover)])
    newgroups = [item for sublist in newgroups for item in sublist]

    regroupedparticles = particles.copy()
    regroupedparticles.sort_values("_rlnDefocusU", inplace=True)

    if "_rlnGroupNumber" in regroupedparticles.columns:
        regroupedparticles.drop("_rlnGroupNumber", axis=1, inplace=True)
        regroupedparticles["_rlnGroupNumber"] = newgroups

    if "_rlnGroupName" in regroupedparticles.columns:
        regroupedparticles.drop("_rlnGroupName", axis=1, inplace=True)
        newgroups = [("group_"+str(i).zfill(4)) for i in newgroups]
        regroupedparticles["_rlnGroupName"] = newgroups
    
    regroupedparticles.sort_index(inplace = True)
    regroupedparticles = regroupedparticles[particles.columns]

    return(regroupedparticles, roundtotal)

"""
--new_optics (also see setparticeoptics())
"""
def makeopticsgroup(particles,metadata,newgroup):
    
    optics = metadata[2]
    
    newoptics = optics.append(optics.loc[len(optics.index)-1], ignore_index = True)
    
    newoptics.loc[len(newoptics.index)-1]["_rlnOpticsGroupName"] = newgroup
    
    opticsnumber = int(newoptics.loc[len(newoptics.index)-1]["_rlnOpticsGroup"]) + 1
    
    newoptics.loc[len(newoptics.index)-1]["_rlnOpticsGroup"] = opticsnumber
    
    return(newoptics, opticsnumber)

"""
--new_optics (also see makeopticsgroup())
"""
def setparticleoptics(particles,column,query,queryexact,opticsnumber):
    
    particlesnewoptics = particles.copy()

    numchanged = countqueryparticles(particles, column, query, queryexact, True)
    
    if not queryexact:
        q = "|".join(query)
        particlesnewoptics.loc[particles[column[0]].str.contains(q), "_rlnOpticsGroup"] = opticsnumber
    else:
        for q in query:
            particlesnewoptics.loc[particles[column[0]]==q, "_rlnOpticsGroup"] = opticsnumber
        
    return(particlesnewoptics, numchanged)

"""
--import_particle_values
"""
def importpartvalues(original_particles, importfrom_particles, columnstoswap):
    # Create a dictionary for fast lookup from importfrom_particles
    lookup_dict = importfrom_particles.set_index('_rlnImageName')[columnstoswap].to_dict('index')

    # Check for duplicates in importfrom_particles
    if importfrom_particles['_rlnImageName'].duplicated().any():
        print("\n>> Error: Duplicate entries found in the star file.\n")
        sys.exit()

    # Perform the swapping of values
    for c in columnstoswap:
        # Map each value, checking if it exists in the dictionary
        original_particles[c] = original_particles['_rlnImageName'].apply(
            lambda x: lookup_dict[x][c] if x in lookup_dict else sys.exit(f"\n>> Error: {x} not found in file that you are importing from.")
        )

    return(original_particles)

"""
--import_mic_values
"""
def importmicvalues(importedparticles, importfrom_particles, column):
    # Extract the simple micrograph name if necessary
    if "/" in importedparticles['_rlnMicrographName'][0]:
        importedparticles["_rlnMicrographNameSimple"] = importedparticles['_rlnMicrographName'].str.split('/').str[-1]
    else:
        importedparticles["_rlnMicrographNameSimple"] = importedparticles['_rlnMicrographName']

    if "/" in importfrom_particles['_rlnMicrographName'][0]:
        importfrom_particles["_rlnMicrographNameSimple"] = importfrom_particles['_rlnMicrographName'].str.split('/').str[-1]
    else:
        importfrom_particles["_rlnMicrographNameSimple"] = importfrom_particles['_rlnMicrographName']

    # Create a lookup dictionary from importfrom_particles
    lookup_dict = importfrom_particles.set_index('_rlnMicrographNameSimple')[column].to_dict()

    # Update values in importedparticles using lookup_dict, with error reporting
    importedparticles[column] = importedparticles['_rlnMicrographNameSimple'].apply(
        lambda x: lookup_dict[x] if x in lookup_dict else sys.exit(f"\n>> Error: Micrograph {x} not found in original file.")
    )

    # Drop the temporary '_rlnMicrographNameSimple' column
    importedparticles.drop("_rlnMicrographNameSimple", axis=1, inplace=True)

    return(importedparticles)

"""
--expand_optics
"""

def expandoptics(original_particles, original_metadata, newdata, newdata_metadata, opticsgrouptoexpand):

    #print(original_metadata)
    #print(original_particles["_rlnMicrographName"])
    #print(original_particles["_rlnOpticsGroup"].head())

    if "_rlnMicrographName" not in original_particles.columns:
        print("\n>> Error: the star file doesn't have a _rlnMicrographName column.\n")
        sys.exit()
    elif "_rlnMicrographName" not in newdata.columns:
        print("\n>> Error: the second star file doesn't have a _rlnMicrographName column.\n")
        sys.exit()

    newmetadata = original_metadata

    opticsgroupnum = int(original_metadata[2].loc[original_metadata[2]["_rlnOpticsGroupName"] == opticsgrouptoexpand]["_rlnOpticsGroup"].tolist()[0])
    opticsgrouplist = original_metadata[2]["_rlnOpticsGroup"].tolist()
    opticsgrouplist = [int(o) for o in opticsgrouplist]

    importopticsnames = newdata_metadata[2]["_rlnOpticsGroupName"].tolist()
    importopticsnums = newdata_metadata[2]["_rlnOpticsGroup"].tolist()
    importopticsnums = [int(o) for o in importopticsnums]
    totalimportoptics = len(importopticsnums)

    #print(opticsgroupnum,opticsgrouplist,importopticsnums,totalimportoptics)

    newoptics = original_metadata[2]
    #print(newoptics["_rlnOpticsGroup"])

    torepeat = []
    for i,o in enumerate(opticsgrouplist):
        i=i+1
        if i < opticsgroupnum:
            torepeat.append(1)
            #continue
        elif i == opticsgroupnum:
            torepeat.append(totalimportoptics)
        else:
            torepeat.append(1)

        #opticsgrouplist[i]+=totalimportoptics

    #print(torepeat)
    newoptics["times"] = torepeat

    newoptics=newoptics.loc[newoptics.index.repeat(newoptics.times)].reset_index(drop=True)

    newoptics["_rlnOpticsGroup"] = range(1,totalimportoptics+len(opticsgrouplist))
    newoptics.drop("times",axis=1, inplace=True)

    newopticsnames = newoptics["_rlnOpticsGroupName"].tolist()

    #print(newoptics)

    j=0
    for i,o in enumerate(newopticsnames):
        if o == opticsgrouptoexpand:
            newopticsnames[i] = importopticsnames[j]
            j+=1

    newoptics["_rlnOpticsGroupName"]=newopticsnames

    newmetadata[2] = newoptics

    #print(newoptics)

    #original_particles["_rlnOpticsGroup"] = pd.to_numeric(original_particles["_rlnOpticsGroup"], downcast="integer")

    particleoptics = original_particles["_rlnOpticsGroup"].tolist()
    newparticleoptics = [int(p) for p in particleoptics]

    for i,p in enumerate(newparticleoptics):
        if p <= opticsgroupnum:
            continue
        else:
            newparticleoptics[i]=str(int(p+totalimportoptics-1))

    original_particles["_rlnOpticsGroup"] = newparticleoptics

    ###############

    #print(newdata)

    newdataoptics = newdata["_rlnOpticsGroup"].tolist()
    newdataoptics = [int(p) for p in newdataoptics]

    for i,p in enumerate(newdataoptics):
        newdataoptics[i]=str(int(p+opticsgroupnum-1))

    newdata["_rlnOpticsGroup"] = newdataoptics

    #print(newdata)

    ####

    #print(original_particles["_rlnOpticsGroup"].head())

    expandedparticles = columnplay.importmicvalues(original_particles, newdata, "_rlnOpticsGroup")

    totaldifferent = 0
    for i, j in zip(original_particles.iterrows(), expandedparticles.iterrows()):
        if i[1]["_rlnOpticsGroup"] != j[1]["_rlnOpticsGroup"]:
            totaldifferent += 1

    print("\n>> The number of particles that have acquired a new optics group number = " + str(totaldifferent) + "\n")

    return(expandedparticles, newmetadata)

"""
--remove_poses
"""
class SelectFromCollection:
    def __init__(self, ax, collection, alpha_other=1):
        self.canvas = ax.figure.canvas
        self.ax = ax
        self.collection = collection
        self.alpha_other = alpha_other
        self.xys = collection.get_offsets()
        self.Npts = len(self.xys)
        self.fc = collection.get_facecolors()
        if len(self.fc) == 0:
            raise ValueError('Collection must have a facecolor')
        elif len(self.fc) == 1:
            self.fc = np.tile(self.fc, (self.Npts, 1))
        
        self.lasso = LassoSelector(ax, onselect=self.onselect, props=dict(color='r'))
        self.ind = []
        self.selected_points = None

    def onselect(self, verts):
        path = Path(verts)
        self.ind = np.nonzero(path.contains_points(self.xys))[0]
        self.fc[:, -1] = self.alpha_other
        self.fc[self.ind, -1] = 1
        self.collection.set_facecolors(self.fc)
        
        # Overlay red points for the selected area
        selected_x = self.xys[self.ind][:, 0]
        selected_y = self.xys[self.ind][:, 1]
        if self.selected_points is not None:
            self.selected_points.remove()
        self.selected_points = self.ax.scatter(selected_x, selected_y, s=3, c='red')
        
        self.canvas.draw_idle()

    def disconnect(self):
        self.lasso.disconnect_events()
        self.fc[:, -1] = 1
        self.collection.set_facecolors(self.fc)
        if self.selected_points is not None:
            self.selected_points.remove()
        self.canvas.draw_idle()

def remove_poses(particles, metadata, outputname, relegateflag):

    x_coordinates = list(map(float, list(particles["_rlnAngleRot"])))
    y_coordinates = list(map(float, list(particles["_rlnAngleTilt"])))

    fig, ax = plt.subplots()

    pts = ax.scatter(x_coordinates, y_coordinates, s=1)
    selector = SelectFromCollection(ax, pts)

    global selected_indices
    selected_indices = []

    def update_plot():
        ax.clear()
        unselected_x = [x_coordinates[i] for i in range(len(x_coordinates)) if i not in selected_indices]
        unselected_y = [y_coordinates[i] for i in range(len(y_coordinates)) if i not in selected_indices]
        ax.scatter(unselected_x, unselected_y, s=1)
        ax.set_title("Press 'enter' to remove selected orientations, 'e' to save and exit")
        ax.set_xlabel("Rot")
        ax.set_ylabel("Tilt")
        selector.__init__(ax, pts)  # Reinitialize the selector
        plt.draw()

    def accept(event):
        
        if event.key == "enter":
            selected_indices.extend(selector.ind)
            selector.disconnect()
            update_plot()

        elif event.key == "e":
            if selected_indices:
                non_selected_indices = [i for i in range(len(x_coordinates)) if i not in selected_indices]
                non_selected_particles = particles.iloc[non_selected_indices]
                plt.close()
                print("\n>> Removed " + str(len(particles.index)-len(non_selected_particles.index)) + " particles out of " + str(len(particles.index)) + ".\n")
                fileparser.writestar(non_selected_particles, metadata, outputname, relegateflag)

    fig.canvas.mpl_connect("key_press_event", accept)
    ax.set_title("Press 'enter' to remove selected orientations.")
    ax.set_xlabel("Rot")
    ax.set_ylabel("Tilt")
    plt.show()


def extractoptics(particles, metadata, queryexact):

    params = argparser.argparse()
    if params["parser_column"] != "" and params["parser_query"] != "":

        query = params["parser_query"]
        escape = ",/"
        query = str.replace(params["parser_query"],escape, ",")
        query = query.split("/")
        for i,q in enumerate(query):
            query[i] = str.replace(q,",", "/")

        column = params["parser_column"].split("/")

    if len(column)>1:
        print("\n>> Error: you have specified two columns. Only specify one if you're extracting from a subset of the data using a query.\n")
        sys.exit()
    else:
        column = makefullname(column[0])

    opticsheaders = metadata[1]
    opticsdata = metadata[2]

    if column not in opticsheaders:
        print(f"\n>> Error: {column} is not in your optics table.\n")
        sys.exit()

    itisnumeric = True
    try:
        pd.to_numeric(opticsdata[column], downcast="float")
    except ValueError:
        itisnumeric = False

    params = argparser.argparse()

    if not queryexact and itisnumeric:
        print("\n----------------------------------------------------------------------")        
        print("\n>> Warning: it looks like this column has numbers but you haven't specified the exact option (--e).\n   Make sure that this is the behavior you intended.\n")
        print("----------------------------------------------------------------------")

    if not queryexact:
        matching_opticsnumbers = opticsdata[opticsdata[column].str.contains('|'.join(query))]['_rlnOpticsGroup']
        non_repeating_values_set = list(set(matching_opticsnumbers))

    else:
        matching_opticsnumbers = opticsdata[opticsdata[column].isin(query)]['_rlnOpticsGroup']
        non_repeating_values_set = list(set(matching_opticsnumbers))

    if len(non_repeating_values_set) == 0:
        print("\n>> Error: No optics groups matched the optics query.\n")
        sys.exit()

    toconcat = [particles[particles["_rlnOpticsGroup"] == q] for q in non_repeating_values_set]
    newparticles = pd.concat(toconcat)

    if newparticles.empty:
        print("\n>> Error: No particles matched the optics query.\n")
        sys.exit()

    extractednumber = len(newparticles.index)

    newopticsdata = opticsdata[opticsdata['_rlnOpticsGroup'].isin(non_repeating_values_set)]
    
    return(newparticles, [metadata[0], metadata[1], newopticsdata, metadata[3], metadata[4]], extractednumber)

def makefullname(col):
    if col.startswith("_rln"):
        return(col)
    elif col.startswith("rln"):
        return("_"+col)
    elif col.startswith("_rn") or col.startswith("rn"):
        print(f"\n>> Error: check the column name {col}.\n")
        sys.exit()
    elif col.startswith("rn") and not col.startswith("rln"):
        print(f"\n>> Error: check the column name {col}.\n")
        sys.exit()
    else:
        return("_rln"+col)