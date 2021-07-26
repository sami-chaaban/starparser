import pandas as pd
import sys

def delcolumn(particles, columns, metadata):
    
    nocolparticles = particles.copy()
    
    for c in columns:
        if c not in nocolparticles:
            print("\n>> Error: the column \"" + c + "\" does not exist.\n")
            sys.exit()
        nocolparticles.drop(c, 1, inplace=True)
        metadata[3].remove(c)
    
    return(nocolparticles, metadata)

def swapcolumns(original_particles, swapfrom_particles, columns):

    if len(original_particles.index) != len(swapfrom_particles.index):
        print("\n>> Error: the star files don't have the same number of particles: " + str(len(original_particles.index)) + " vs " + str(len(swapfrom_particles.index)) + ".\n")
        sys.exit()
    
    swappedparticles = original_particles.copy()
    
    for c in columns:
        if c not in original_particles:
            print("\n>> Error: the column \"" + c + "\" does not exist in the original star file.\n")
            sys.exit()
        if c not in swapfrom_particles:
            print("\n>> Error: the column \"" + c + "\" does not exist in the second star file.\n")
            sys.exit()
        columnindex = original_particles.columns.get_loc(c)
        swappedparticles.drop(c,1,inplace=True)
        swappedparticles.insert(columnindex, c, swapfrom_particles[c].values.tolist())
    
    return(swappedparticles)

def importmicvalues(importedparticles, importfrom_particles, column):

    ####

    dropflag = False

    if "/" in importedparticles['_rlnMicrographName'][0]:
        importedparticles["_rlnMicrographNameSimple"] = importedparticles['_rlnMicrographName']
        for idx, row in importedparticles.iterrows():
            micname = importedparticles.loc[idx,"_rlnMicrographName"]
            importedparticles.loc[idx,"_rlnMicrographNameSimple"] = micname[micname.rfind("/")+1:]

        importedparticles = importedparticles.set_index('_rlnMicrographNameSimple')

        dropflag = True

    else:

        importedparticles = importedparticles.set_index('_rlnMicrographName')

    ##

    if "/" in importfrom_particles['_rlnMicrographName'][0]:
        importfrom_particles["_rlnMicrographNameSimple"] = importfrom_particles['_rlnMicrographName']
        for idx, row in importfrom_particles.iterrows():
            micname = importfrom_particles.loc[idx,"_rlnMicrographName"]
            importfrom_particles.loc[idx,"_rlnMicrographNameSimple"] = micname[micname.rfind("/")+1:]

        importfrom_particles = importfrom_particles[["_rlnMicrographNameSimple", column]]
        importfrom_particles = importfrom_particles.set_index('_rlnMicrographNameSimple')

    else:

        importfrom_particles = importfrom_particles[["_rlnMicrographName", column]]
        importfrom_particles = importfrom_particles.set_index('_rlnMicrographName')

    ####

    importedparticles.update(importfrom_particles)

    importedparticles.reset_index(inplace=True)

    if dropflag:

        importedparticles.drop("_rlnMicrographNameSimple", 1, inplace=True)
    
    return(importedparticles)

def renumbercol(datatable, columns):
    
    newdatatable = datatable[:3]

    newcount = 1

    for i,L in enumerate(datatable[2:]):

        if L in columns:

            if i != 0:
                newdatatable = newdatatable[:-1]
                newcount -= 1
            else:    
                newdatatable = newdatatable[:-1]
            continue

        if L[0] == '#' and i != 1:
            newdatatable.append('#' + str(newcount))
            newcount += 1
            continue

        if i != 1:
            newdatatable.append(L)
            
    return(newdatatable)

def operate(particles,column,operator,value):

    try:
        particles[column] = pd.to_numeric(particles[column], downcast="float")
    except ValueError:
        print("\n>> Error: Could not interpret the values in " + column + " as numbers.\n")
        sys.exit()

    if operator == "multiply":
        print("\n>> Multiplying  all values in " + column + " by " + str(value) + ".")
        particles[column] = particles[column] * value

    elif operator == "divide":
        print("\n>> Dividing  all values in " + column + " by " + str(value) + ".")
        particles[column] = particles[column] / value

    elif operator == "add":
        print("\n>> Adding " + str(value) + " to all values in " + column + ".")
        particles[column] = particles[column] + value

    elif operator == "subtract":
        print("\n>> Subtracting " + str(value) + " from all values in " + column + ".")
        particles[column] = particles[column] - value

    return(particles)

def operatecolumns(particles,column1,column2,newcolumn,operator,metadata):

    try:
        particles[column1] = pd.to_numeric(particles[column1], downcast="float")
    except ValueError:
        print("\n>> Error: Could not interpret the values in " + column1 + " as numbers.\n")
        sys.exit()
    try:
        particles[column2] = pd.to_numeric(particles[column2], downcast="float")
    except ValueError:
        print("\n>> Error: Could not interpret the values in " + column2 + " as numbers.\n")
        sys.exit()

    if operator == "multiply":
        print("\n>> Multiplying " + column1 + " by " + column2 + " and storing the result in " + newcolumn + ".")
        particles[newcolumn] = particles[column1] * particles[column2]

    elif operator == "divide":
        print("\n>> Dividing  all values in " + column1 + " by " + column2 + " and storing the result in " + newcolumn + ".")
        particles[newcolumn] = particles[column1] / particles[column2]

    elif operator == "add":
        print("\n>> Adding " + column2 + " to all values in " + column1 + " and storing the result in " + newcolumn + ".")
        particles[newcolumn] = particles[column1] + particles[column2]

    elif operator == "subtract":
        print("\n>> Subtracting " + column2 + " from all values in " + column1 + " and storing the result in " + newcolumn + ".")
        particles[newcolumn] = particles[column1] - particles[column2]

    metadata[3].append(newcolumn)

    return(particles,metadata)
  
def writecol(particles, columns):
    
    outputs = []
    
    for c in columns:
        
        tosave = particles[c].tolist()
        
        outputname = c[4:] + ".txt"
        outputs.append(outputname)
        
        output = open(outputname,"w")
        
        for s in tosave:
            output.write(s)
            output.write("\n")
        
        output.close()
    
    return(outputs)

def replacecolumn(particles,replacecol,newcol):
    columnindex = particles.columns.get_loc(replacecol)
    particles.drop(replacecol, 1, inplace=True)
    particles.insert(columnindex, replacecol, newcol)
    return(particles)

def copycolumn(particles,sourcecol,targetcol,metadata):
    if targetcol not in particles:
        print("\n>> Creating a new column: " + targetcol + ".")
        metadata[3].append(targetcol)
    else:
        print("\n>> Replacing values in " + targetcol + " with " + sourcecol + ".")

    particles[targetcol] = particles[sourcecol]

    return(particles)

def resetcolumn(particles,column,value):

    print("\n>> Replacing all values in " + column + " with " + value + ".")
    particles[column]=value
    return(particles)