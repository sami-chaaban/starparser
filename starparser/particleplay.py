import pandas as pd

def limitparticles(particles, column, limit, operator):
    
    tempcolumnname = column + "_float"
    particles[tempcolumnname] = particles[column]
    try:
        particles[tempcolumnname] = pd.to_numeric(particles[tempcolumnname], downcast="float")
    except:
        print("\n>> Error: could not convert the values in this column to numbers.\n")
        sys.exit()
    limitedparticles = particles.copy()

    if operator == "lt":
        limitedparticles = limitedparticles[limitedparticles[tempcolumnname]<limit]
    elif operator == "gt":
        limitedparticles = limitedparticles[limitedparticles[tempcolumnname]>limit]
    
    particles.drop(tempcolumnname,1, inplace=True)
    limitedparticles.drop(tempcolumnname,1, inplace=True)

    if len(limitedparticles.index) == 0:
        if operator == "lt":
                print("\n>> Error: there are no particles that match this criterion: " + column + " less than " + str(limit) + ".\n")
        if operator == "gt":
                print("\n>> Error: there are no particles that match this criterion: " + column + " greater than " + str(limit) + ".\n")
        sys.exit()
    
    return(limitedparticles)

def delparticles(particles, columns, query, queryexact):
    
    purgedparticles = particles.copy()
    
    if len(columns)>1:
        print("\n>> Error: you have specified two columns. You can't if you're querying to delete.\n")
        sys.exit()

    if columns[0] in ["_rlnClassNumber", "_rlnGroupNumber", "_rlnNrOfSignificantSamples", "_rlnOpticsGroup"] and not queryexact:
        print("\n----------------------------------------------------------------------")        
        print("\n>> Warning: it looks like this column has integers but you haven't specified the exact option (--e). Make sure that this is the behavior you intended.\n")
        print("----------------------------------------------------------------------")

    if not queryexact:
        q = "|".join(query)
        purgedparticles.drop(purgedparticles[purgedparticles[columns[0]].str.contains(q)].index , 0,inplace=True)
    else:
        for q in query:
            purgedparticles.drop(purgedparticles[purgedparticles[columns[0]]==q].index , 0,inplace=True)
    
    return(purgedparticles)

def delduplicates(particles, column):

    return(particles.drop_duplicates(subset=[column]))

def delmics(particles, micstodelete):
    purgedparticles = particles.copy()
    m = "|".join(micstodelete)
    purgedparticles.drop(purgedparticles[purgedparticles["_rlnMicrographName"].str.contains(m)].index , 0,inplace=True)    
    return(purgedparticles)

def extractparticles(particles, columns, query, queryexact):
    
    if len(columns)>1:
        print("\n>> Error: you have specified two columns. Only specify one if you're extracting from a subset of the data using a query.\n")
        sys.exit()

    if columns[0] in ["_rlnClassNumber", "_rlnGroupNumber", "_rlnNrOfSignificantSamples", "_rlnOpticsGroup"] and not queryexact and not params["parser_splitoptics"] and not params["parser_classproportion"]:
        print("\n----------------------------------------------------------------------")        
        print("\n>> Warning: it looks like this column has integers but you haven't specified the exact option (--e). Make sure that this is the behavior you intended.\n")
        print("----------------------------------------------------------------------")

    if not queryexact:
        extractedparticles = particles.copy()
        q = "|".join(query)
        extractedparticles.drop(extractedparticles[~extractedparticles[columns[0]].str.contains(q)].index, 0,inplace=True)
    else:
        toconcat = [particles[particles[columns[0]] == q] for q in query]
        extractedparticles = pd.concat(toconcat)

    extractednumber = len(extractedparticles.index)
    
    return(extractedparticles, extractednumber)

def checksubset(particles, params, queryexact):
    
    if params["parser_column"] != "" and params["parser_query"] != "":
        query = params["parser_query"].split("/")
        columns = params["parser_column"].split("/")
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

    if columns[0] in ["_rlnClassNumber", "_rlnGroupNumber", "_rlnNrOfSignificantSamples", "_rlnOpticsGroup", "_rlnHelicalTubeID"] and not queryexact:
        print("\n----------------------------------------------------------------------")        
        print("\n>> Warning: it looks like this column has integers but you haven't specified the \"exact\" option (--e, see documentation). Make sure that this is the behavior you intended.\n")
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
        regroupedparticles.drop("_rlnGroupNumber", 1, inplace=True)
        regroupedparticles["_rlnGroupNumber"] = newgroups

    if "_rlnGroupName" in regroupedparticles.columns:
        regroupedparticles.drop("_rlnGroupName", 1, inplace=True)
        newgroups = [("group_"+str(i).zfill(4)) for i in newgroups]
        regroupedparticles["_rlnGroupName"] = newgroups
    
    regroupedparticles.sort_index(inplace = True)
    regroupedparticles = regroupedparticles[particles.columns]

    return(regroupedparticles, roundtotal)
    
def makeopticsgroup(particles,metadata,newgroup):
    
    optics = metadata[2]
    
    newoptics = optics.append(optics.loc[len(optics.index)-1], ignore_index = True)
    
    newoptics.loc[len(newoptics.index)-1]["_rlnOpticsGroupName"] = newgroup
    
    opticsnumber = int(newoptics.loc[len(newoptics.index)-1]["_rlnOpticsGroup"]) + 1
    
    newoptics.loc[len(newoptics.index)-1]["_rlnOpticsGroup"] = opticsnumber
    
    return(newoptics, opticsnumber)
    
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