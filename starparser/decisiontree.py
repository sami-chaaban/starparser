import sys
import os.path
import pandas as pd

from starparser import argparser
from starparser import columnplay
from starparser import fileparser
from starparser import particleplay
from starparser import plots
from starparser import specialparticles
from starparser import splits

def decide():

    ##############################################################

    params = argparser.argparse()
    
    #Sanity check
    
    if 'file' not in params:
        print("\n>> Error: no filename entered. See the help page (-h).\n")
        sys.exit()
        
    if "_rlnOpticsGroup" in params["parser_column"] and params["parser_relegate"]:
        print("\n>> Error: cannot have the relegate option and the delete OpticsGroup column at the same time (the former will do the latter already).\n")
        sys.exit()

    if params["parser_outtype"] not in ["png", "pdf", "jpg", "svg"]:
        print("\n>> Error: choose between png, pdf, svg, and jpg for the plot filetype.\n")
        sys.exit()
        
    ################################################################
    
    #Essential variables
    
    filename = params['file']

    if params['file'] == "":
        print("\n>> Error: enter a star file with --i.\n")
        sys.exit();

    if not os.path.isfile(filename):
        print("\n>> Error: \"" + filename + "\" does not exist.\n")
        sys.exit();

    outtype = params["parser_outtype"]

    queryexact = params["parser_exact"]
    if queryexact:
        print("\n>> You have asked starparser to look for exact matches between the queries and values.")
    elif params["parser_splitoptics"] or params["parser_classdistribution"] or params["parser_splitclasses"]:
        queryexact = True
    
    #####################################################################
    
    #Set up jobs that don't require initialization
    
    if params["parser_classdistribution"] != "":
        if params["parser_classdistribution"] in ["all", "All", "ALL"]:
            plots.plotclassparts(filename, [-1], queryexact, outtype)
        else:
            plots.plotclassparts(filename,params["parser_classdistribution"].split("/"), queryexact, outtype)
        sys.exit()
    
    #########################################################################
    
    #Initialize variables

    print("\n>> Reading " + filename)

    if params["parser_optless"]: #add dummy optics table
        allparticles, metadata = fileparser.getparticles_dummyoptics(filename)
        #print("\n>> Created a dummy optics table to read this star file.")
    else:
        allparticles, metadata = fileparser.getparticles(filename)

    totalparticles = len(allparticles.index)
    
    if params["parser_query"] != "":
        query = params["parser_query"].split("/")
    
    if params["parser_column"] != "":
        columns = params["parser_column"].split("/")
        
        for c in columns:
            if c not in allparticles.columns:
                print("\n>> Error: the column [" + str(c) + "] does not exist in your star file.\n")
                sys.exit()
                
    else:
        
        columns = ""

    if params["parser_optless"]:
        relegateflag = True
    else:
        relegateflag = params["parser_relegate"]
    
    #####################################################################
        
    #Set up jobs that don't require a subset (faster this way)

    if params["parser_countme"] and params["parser_column"] != "" and params["parser_query"] != "":
        particleplay.countqueryparticles(allparticles, columns, query, queryexact, False)
        sys.exit()
    elif params["parser_countme"]:
        print('\n>> There are ' + str(totalparticles) + ' particles in total.\n') 
        sys.exit()
        
    if params["parser_delcolumn"] != "":
        columns = params["parser_delcolumn"].split("/")
        newparticles, metadata = columnplay.delcolumn(allparticles, columns, metadata)
        print("\n>> Removed the columns " + str(columns))
        fileparser.writestar(newparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()
        
    if params["parser_delparticles"]:
        if params["parser_query"] == "" or params["parser_column"] == "":
            print("\n>> Error: provide a column (--c) and query (--q) to find specific particles to remove.\n")
            sys.exit()
        newparticles = particleplay.delparticles(allparticles, columns, query, queryexact)
        purgednumber = len(allparticles.index) - len(newparticles.index)
        print("\n>> Removed " + str(purgednumber) + " particles (out of " + str(totalparticles) + ", " + str(round(purgednumber*100/totalparticles,1)) + "%) that matched " + str(query) + " in the column " + params["parser_column"] + ".")
        fileparser.writestar(newparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_delduplicates"] != "":
        column = params["parser_delduplicates"]
        if column not in allparticles:
            print("\n>> Error: the column " + str(column) + " does not exist in your star file.\n")
            sys.exit()
        newparticles = particleplay.delduplicates(allparticles, column)
        purgednumber = len(allparticles.index) - len(newparticles.index)
        newtotal = len(newparticles.index)
        print("\n>> Removed " + str(purgednumber) + " particles (out of " + str(totalparticles) + ", " + str(round(purgednumber*100/totalparticles,1)) + "%) that were duplicates based on the " + column + " column.")
        print(">> The new total is " + str(newtotal) + " particles.")
        fileparser.writestar(newparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_delmics"]:
        if params["parser_query"] != "" or params["parser_column"] != "":
            print("\n>> Error: you cannot provide a query to the delete_mics_fromlist option.\n")
            sys.exit()
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to match micrographs.\n")
            sys.exit()
        file2 = params["parser_file2"]
        if not os.path.isfile(file2):
            print("\n>> Error: \"" + file2 + "\" does not exist.\n")
            sys.exit();
        with open(file2) as f:
            micstodelete = [line.split()[0] for line in f]
        newparticles = particleplay.delmics(allparticles,micstodelete)
        purgednumber = len(allparticles.index) - len(newparticles.index)
        print("\n>> Removed " + str(purgednumber) + " particles (out of " + str(totalparticles) + ", " + str(round(purgednumber*100/totalparticles,1)) + "%) that matched the micrographs in " + file2 + ".")
        fileparser.writestar(newparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()
        
    if params["parser_swapcolumns"] != "":
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to swap columns from.\n")
            sys.exit()
        file2 = params["parser_file2"]
        if not os.path.isfile(file2):
            print("\n>> Error: \"" + file2 + "\" does not exist.\n")
            sys.exit();
        otherparticles, metadata2 = fileparser.getparticles(file2)
        columnstoswap = params["parser_swapcolumns"].split("/")
        swappedparticles = columnplay.swapcolumns(allparticles, otherparticles, columnstoswap)
        print("\n>> Swapped in " + str(columnstoswap) + " from " + file2)
        fileparser.writestar(swappedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_importmicvalues"] != "":
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to import values from.\n")
            sys.exit()
        file2 = params["parser_file2"]
        if not os.path.isfile(file2):
            print("\n>> Error: \"" + file2 + "\" does not exist.\n")
            sys.exit();
        otherparticles, metadata2 = fileparser.getparticles(file2)
        columnstoimport = params["parser_importmicvalues"].split("/")

        for column in columnstoimport:
            if column not in allparticles:
                print("\n>> Error: the column \"" + column + "\" does not exist in the original star file.\n")
                sys.exit()
            if column not in otherparticles:
                print("\n>> Error: the column \"" + column + "\" does not exist in the second star file.\n")
                sys.exit()

        if "_rlnMicrographName" not in allparticles:
            print("\n>> Error: _rlnMicrographName does not exist in the original star file.\n")
            sys.exit()
        if "_rlnMicrographName" not in otherparticles:
            print("\n>> Error: _rlnMicrographName does not exist in the second star file.\n")
            sys.exit()

        print("\n>> Importing " + str(columnstoimport) + " from " + file2)

        #this is very inefficient
        importedparticles = allparticles.copy()
        for column in columnstoimport:
            importedparticles = columnplay.importmicvalues(importedparticles, otherparticles, column)

        fileparser.writestar(importedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_importpartvalues"] != "":
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to import values from.\n")
            sys.exit()
        file2 = params["parser_file2"]
        if not os.path.isfile(file2):
            print("\n>> Error: \"" + file2 + "\" does not exist.\n")
            sys.exit();
        otherparticles, metadata2 = fileparser.getparticles(file2)
        columnstoimport = params["parser_importpartvalues"].split("/")

        for column in columnstoimport:
            if column not in allparticles:
                print("\n>> Error: the column \"" + column + "\" does not exist in the original star file.\n")
                sys.exit()
            if column not in otherparticles:
                print("\n>> Error: the column \"" + column + "\" does not exist in the second star file.\n")
                sys.exit()

        if "_rlnImageName" not in allparticles:
            print("\n>> Error: _rlnImageName does not exist in the original star file.\n")
            sys.exit()
        if "_rlnImageName" not in otherparticles:
            print("\n>> Error: _rlnImageName does not exist in the second star file.\n")
            sys.exit()

        print("\n>> Importing " + str(columnstoimport) + " from " + file2)

        importedparticles = particleplay.importpartvalues(allparticles, otherparticles, columnstoimport)

        fileparser.writestar(importedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_operate"] != "":
        if len(params["parser_operate"].split("*")) == 2:
            arguments = params["parser_operate"].split("*")
            operator = "multiply"
        elif len(params["parser_operate"].split("/")) == 2:
            arguments = params["parser_operate"].split("/")
            operator = "divide"
        elif len(params["parser_operate"].split("+")) == 2:
            arguments = params["parser_operate"].split("+")
            operator = "add"
        elif len(params["parser_operate"].split("-")) == 2:
            arguments = params["parser_operate"].split("-")
            operator = "subtract"
        else:
            print("\n>> Error: the argument to pass is column[operator]value (e.g. _rlnHelicalTrackLength*0.25).\n")
            sys.exit()
        column, value = arguments
        try:    
            value = float(value)
        except ValueError:
            print("\n>> Error: Could not interpret \"" + value + "\" as numeric.\n")
            sys.exit()      
        if column not in allparticles:
            print("\n>> Error: Could not find the column " + column + " in the star file.\n")
            sys.exit()  

        operatedparticles = columnplay.operate(allparticles,column,operator,value)
        fileparser.writestar(operatedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_operatecolumns"] != "":
        if len(params["parser_operatecolumns"].split("*")) == 2:
            arguments = params["parser_operatecolumns"].split("*")
            operator = "multiply"
        elif len(params["parser_operatecolumns"].split("/")) == 2:
            arguments = params["parser_operatecolumns"].split("/")
            operator = "divide"
        elif len(params["parser_operatecolumns"].split("+")) == 2:
            arguments = params["parser_operatecolumns"].split("+")
            operator = "add"
        elif len(params["parser_operatecolumns"].split("-")) == 2:
            arguments = params["parser_operatecolumns"].split("-")
            operator = "subtract"
        else:
            print("\n>> Error: the argument to pass is column1[operator]column2=newcolumn (e.g. _rlnCoordinateX*_rlnOriginX=_rlnShifted).\n")
            sys.exit()
        column1, secondhalf = arguments
        column2 = secondhalf.split("=")[0]
        newcolumn = secondhalf.split("=")[1] 
        if column1 not in allparticles:
            print("\n>> Error: Could not find the column " + column1 + " in the star file.\n")
            sys.exit()
        elif column2 not in allparticles:
            print("\n>> Error: Could not find the column " + column2 + " in the star file.\n")
            sys.exit()
        elif newcolumn in allparticles:
            print("\n>> Error: The column " + newcolumn + " already exists in the star file.\n")
            sys.exit()
        operatedparticles, newmetadata = columnplay.operatecolumns(allparticles,column1,column2,newcolumn,operator,metadata)
        fileparser.writestar(operatedparticles, newmetadata, params["parser_outname"], relegateflag)
        sys.exit()
        
    if params["parser_findshared"] != "":
        columntocheckunique = params["parser_findshared"]
        if columntocheckunique not in allparticles.columns:
            print("\n>> Error: could not find the " + columntocheckunique + " column in " + filename + ".\n")
            sys.exit()
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to compare to.\n")
            sys.exit()
        file2 = params["parser_file2"]
        if not os.path.isfile(file2):
            print("\n>> Error: \"" + file2 + "\" does not exist.\n")
            sys.exit();
        otherparticles, f2metadata = fileparser.getparticles(file2)
        unsharedparticles = allparticles[~allparticles[columntocheckunique].isin(otherparticles[columntocheckunique])]
        sharedparticles = allparticles[allparticles[columntocheckunique].isin(otherparticles[columntocheckunique])]
        if params["parser_findshared"] != "":
            print("\nShared: \n-------\n" + str(len(sharedparticles.index)) + " particles are shared between " + filename + " and " + file2 + " in the " + str(columntocheckunique) + " column.\n")
            fileparser.writestar(sharedparticles, metadata, "shared.star", relegateflag)
            print("Unique: \n-------\n·" + filename + ": " + str(len(unsharedparticles.index)) + " particles (these will be written to unique.star)\n·" + file2 + ": " + str(len(otherparticles.index) - len(sharedparticles.index)) + " particles\n")
            fileparser.writestar(unsharedparticles, metadata, "unique.star", relegateflag)
        sys.exit()

    if params["parser_findnearby"] != -1:
        threshdist = float(params["parser_findnearby"])
        if threshdist < 0:
             print("\n>> Error: distance cannot be negative.\n")    
             sys.exit()       
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file to check the particle distances with --f.\n")
            sys.exit()
        if not os.path.isfile(params["parser_file2"]):
            print("\n>> Error: \"" + params["parser_file2"] + "\" does not exist.\n")
            sys.exit();

        nearparticles, nearmetadata = fileparser.getparticles(params["parser_file2"])
        farparticles, closeparticles, distances = specialparticles.findnearby(allparticles, nearparticles, threshdist)

        fig = plt.figure()
        plt.hist(distances, bins='fd', color = 'k', alpha=0.5)
        plt.axvline(x=threshdist, linestyle='--', color = 'maroon')
        plt.ylabel('Frequency')
        plt.xlabel('Nearest distance')
        plots.outputfig(fig, "Particle_distances", outtype)

        fileparser.writestar(closeparticles, metadata, "particles_close.star", relegateflag)
        fileparser.writestar(farparticles, metadata, "particles_far.star", relegateflag)

        sys.exit()

    if params["parser_fetchnearby"] != "":
        retrieveparams = params["parser_fetchnearby"].split("/")
        if len(retrieveparams) < 2:
            print("\n>> Error: provide argument in this format: distance/column(s) (e.g. 300/_rlnClassNumber).")
            sys.exit()
        columnstoretrieve = retrieveparams[1:]
        for c in columnstoretrieve:
            if c not in allparticles:
                print("\n>> Error: " + c + " does no exist in the input star file.\n")
                sys.exit()
                # print("\n>> Warning: " + c + " does not exist in the input star file. It will be created.\n")
                # allparticles.loc[:,c] = "" #creates slice warning
                # metadata[3].append(c)
        threshdist = float(retrieveparams[0])
        if threshdist < 0:
             print("\n>> Error: distance cannot be negative.\n")    
             sys.exit()
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to retrieve values from.\n")
            sys.exit()
        if not os.path.isfile(params["parser_file2"]):
            print("\n>> Error: \"" + params["parser_file2"] + "\" does not exist.\n")
            sys.exit();
        nearparticles, nearmetadata = fileparser.getparticles(params["parser_file2"])
        for c in columnstoretrieve:
            if c not in nearparticles:
                print("\n>> Error: " + c + " does not exist in the second star file.\n")
                sys.exit()
        print("\n>> Fetching " + str(columnstoretrieve) + " values from particles within " + str(threshdist) + " pixels.\n")
        stolenparticles = specialparticles.fetchnearby(allparticles, nearparticles, threshdist, columnstoretrieve)
        fileparser.writestar(stolenparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_cluster"] != "":
        retrieveparams = params["parser_cluster"].split("/")
        if len(retrieveparams) != 2:
            print("\n>> Error: provide argument in this format: threshold-distance/minimum-per-cluster (e.g. 400/4).")
            sys.exit()
        threshold = float(retrieveparams[0])
        minimum = int(retrieveparams[1])
        print("\n>> Extracting particles that have at least " + str(minimum) + " neighbors within " + str(threshold) + " pixels.\n")
        clusterparticles = specialparticles.getcluster(allparticles, threshold,minimum)
        fileparser.writestar(clusterparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()
        
    if params["parser_classproportion"]:
        if params["parser_query"] == "":
            print("\n>> Error: you have not entered a query.\n")
            sys.exit()
        elif params["parser_column"] == "":
            print("\n>> Error: you have not entered a column.\n")
            sys.exit()
        plots.classproportion(allparticles, columns, query, queryexact, outtype)
        sys.exit()
        
    if params["parser_newoptics"] !="":
        newgroup = params["parser_newoptics"]
        newoptics, opticsnumber = particleplay.makeopticsgroup(allparticles,metadata,newgroup)
        metadata[2] = newoptics
        if params["parser_column"] == "" or params["parser_query"] == "":
            print("\n>> Error: you did not enter either an optics group name, column name, or query(ies).\n")
            sys.exit()
        particlesnewoptics, newopticsnumber = particleplay.setparticleoptics(allparticles,columns,query,queryexact,str(opticsnumber))
        print("\n>> Created optics group called " + newgroup + " (optics group " + str(opticsnumber)+") for the " + str(newopticsnumber) + " particles that match " + str(query) + " in the column " + str(columns))
        fileparser.writestar(particlesnewoptics,metadata,params["parser_outname"],False)
        sys.exit()

    if params["parser_limitparticles"] != "":
        parsedinput = params["parser_limitparticles"].split("/")
        if len(parsedinput) > 3:
            print("\n>> Error: provide argument in this format: column/operator/value (e.g. _rlnDefocusU/lt/40000).")
            sys.exit()
        columntocheck = parsedinput[0]
        operator = parsedinput[1]
        limit = float(parsedinput[2])
        if operator not in ["lt", "gt"]:
            print("\n>> Error: use \"lt\" or \"gt\" as the operator for less than and greater than, respectively.")
            sys.exit()
        limitedparticles = particleplay.limitparticles(allparticles, columntocheck, limit, operator)
        if operator == "lt":
            print("\n>> Extracted " + str(len(limitedparticles.index)) + " particles (out of " + str(totalparticles) + ", " + str(round(len(limitedparticles.index)*100/totalparticles,1)) + "%) that have " + str(columntocheck) + " values less than " + str(limit))
        elif operator == "gt":
            print("\n>> Extracted " + str(len(limitedparticles.index)) + " particles (out of " + str(totalparticles) + ", " + str(round(len(limitedparticles.index)*100/totalparticles,1)) + "%) that have " + str(columntocheck) + " values greater than " + str(limit))
        fileparser.writestar(limitedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_randomset"] != -1:
        numrandom = params["parser_randomset"]
        if numrandom == 0:
            print("\n>> Error: you cannot pass 0 particles.\n")
        if numrandom > len(allparticles.index):
            print("\n>> Error: the number of particles you want to randomly extract cannot be greater than the total number of particles (" + str(len(allparticles.index)) + ").\n")
        if params["parser_column"] == "" and params["parser_query"] == "":
            print("\n>> Creating a random set of " + str(numrandom) + " particles.")
            fileparser.writestar(allparticles.sample(n = numrandom), metadata, params["parser_outname"], relegateflag)
        elif params["parser_column"] == "" or params["parser_query"] == "":
            print("\n>> Error: check that you have passed the column and query arguments correctly.\n")
        else:
            for q in query:
                print("\n>> Creating a random set of " + str(numrandom) + " particles that match " + q)
                randomsettowrite, totalnum = particleplay.extractparticles(allparticles,columns,[q],queryexact)
                if totalnum < numrandom and totalnum != 0:
                    print("\n>> Warning: the query " + q + " has less particles than the requested number!\n")
                elif totalnum == 0:
                    print("\n>> Error: the query " + q + " has 0 particles in the specified column.\n")
                    sys.exit()
                fileparser.writestar(randomsettowrite.sample(n = numrandom), metadata, q+"_"+str(numrandom)+".star", relegateflag)
        sys.exit()

    if params["parser_split"] != -1:
        numsplits = params["parser_split"]
        if numsplits == 1:
            print("\n>> Error: you cannot split into 1 part.\n")
            sys.exit()
        if numsplits > len(allparticles.index):
            print("\n>> Error: you cannot split into more parts than there are particles.\n")
            sys.exit()
        splitstars = splits.splitparts(allparticles,numsplits)
        print("\n")
        fill = len(str(len(splitstars)))
        for i,s in enumerate(splitstars):
            print(">> There are " + str(len(s.index)) + " particles in file " + str(i+1))
            fileparser.writestar(s, metadata, filename[:-5]+"_split-"+str(i+1).zfill(fill)+".star", relegateflag)
        sys.exit()

    if params["parser_splitoptics"]:
        splits.splitbyoptics(allparticles,metadata,queryexact)
        sys.exit()

    if params["parser_splitclasses"]:
        if "_rlnClassNumber" not in allparticles:
            print("\n>> Error: _rlnClassNumber does not exist in the star file.")
        splits.splitbyclass(allparticles,metadata,queryexact,relegateflag)
        sys.exit()

    if params["parser_getindex"]:
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f that has the list of values.\n")
            sys.exit()
        with open(params["parser_file2"]) as f:
            indicestoget = [line.split()[0] for line in f]
        indicestoget = [(int(i)-1) for i in indicestoget]
        if max(indicestoget)+1 > len(allparticles.index):
            print("\n>> Error: the index " + str(max(indicestoget)+1) + " is out of bounds (the last index in your star file is " + str(len(allparticles.index)) + ").\n")
            sys.exit()
        print("\n>> Extracting " + str(len(indicestoget)) + " particles (" + str(round(100*len(indicestoget)/len(allparticles.index),1)) + "%) that match the indices.")
        fileparser.writestar(allparticles.iloc[indicestoget], metadata, params["parser_outname"], relegateflag)
        sys.exit()   

    if params["parser_insertcol"] != "":
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f that has the list of values.\n")
            sys.exit()
        insertcol = params["parser_insertcol"]
        if insertcol in allparticles.columns:
            print("\n>> Error: the column " + str(insertcol) + " already exists in your star file. Use --replace_column if you would like to replace it.\n")
            sys.exit()
        newcolfile = params["parser_file2"]
        with open(newcolfile) as f:
            newcolvalues = [line.split()[0] for line in f]
        if len(newcolvalues) != len(allparticles.index):
            print("\n>> Error: your star file has " + str(len(allparticles.index)) + " values while your second file has " + str(len(newcolvalues)) + " values.\n")
            sys.exit()
        print("\n>> Creating the column " + insertcol + " with the values in " + newcolfile + ".")
        allparticles[insertcol]=newcolvalues
        metadata[3].append(insertcol)
        fileparser.writestar(allparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_comparecoords"] != "":
        if params["parser_file2"] == "":
            file2particles = pd.DataFrame({'A' : []})
        else:
            file2particles, metadata = fileparser.getparticles(params["parser_file2"])
        currentparams = params["parser_comparecoords"].split("/")
        numtoplot = currentparams[0]
        if numtoplot in ["all", "All", "ALL"]:
            numtoplot = -1
        else:
            try:
                numtoplot = int(numtoplot)
            except ValueError:
                print("\n>> Error: provide a number of micrographs to plot or pass \"all\" to plot all micrographs.\n")
                sys.exit()
        if numtoplot == 0:
            print("\n>> Error: provide a number of micrographs to plot or pass \"all\" to plot all micrographs.\n")
            sys.exit()
        if len(currentparams) > 1:
            circlesize = float(currentparams[1])
        else:
            circlesize = 80

        if not file2parts.empty:
            if numtoplot != -1:
                print("\n>> Plotting coordinates from the star file (red circles) and second file (blue circles) for " + str(numtoplot) + " micrographs.")
            else:
                print("\n>> Plotting coordinates from the star file (red circles) and second file (blue circles) for " + str(len(file1mics)) + " micrographs.")
        else:
            if numtoplot != -1:
                print("\n>> Plotting coordinates from the star file (red circles) for " + str(numtoplot) + " micrographs.")
            else:
                print("\n>> Plotting coordinates from the star file (red circles) for " + str(len(file1mics)) + " micrographs.")

        plots.comparecoords(allparticles, file2particles, numtoplot, circlesize)
        sys.exit()

    if params["parser_replacecol"] != "":
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f that has the list of values.\n")
            sys.exit()
        replacecol = params["parser_replacecol"]
        if replacecol not in allparticles.columns:
            print("\n>> Error: the column " + str(replacecol) + " does not exist in your star file.\n")
            sys.exit()
        newcolfile = params["parser_file2"]
        with open(newcolfile) as f:
            newcol = [line.split()[0] for line in f]
        if len(newcol) != len(allparticles.index):
            print("\n>> Error: your star file has " + str(len(allparticles.index)) + " values while your second file has " + str(len(newcol)) + " values.\n")
            sys.exit()
        print("\n>> Replacing values in the column " + replacecol + " with those in " + newcolfile + ".")
        replacedstar = columnplay.replacecolumn(allparticles,replacecol,newcol)
        fileparser.writestar(replacedstar, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_copycol"] != "":

        inputparams = params["parser_copycol"].split("/")
        if len(inputparams) != 2:
            print("\n>> Error: the input should be source-column/target-column.\n")
            sys.exit()
        sourcecol, targetcol = inputparams
        if sourcecol not in allparticles:
            print("\n>> Error: " + sourcecol + " does not exist in the star file.\n")
            sys.exit()
        copiedstar = columnplay.copycolumn(allparticles,sourcecol,targetcol,metadata)
        fileparser.writestar(copiedstar, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_resetcol"] != "":

        inputparams = params["parser_resetcol"].split("/")
        if len(inputparams) != 2:
            print("\n>> Error: the input should be column-name/value.\n")
            sys.exit()
        columntoreset, value = inputparams
        if columntoreset not in allparticles:
            print("\n>> Error: " + columntoreset + " does not exist in the star file.\n")
            sys.exit()
        resetstar = columnplay.resetcolumn(allparticles,columntoreset,value)
        fileparser.writestar(resetstar, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_sort"] != "":
        inputparams = params["parser_sort"].split("/")
        sortcol = inputparams[0]
        if sortcol not in allparticles.columns:
            print("\n>> Error: the column " + str(sortcol) + " does not exist in your star file.\n")
            sys.exit()
        if len(inputparams) == 1:
            try:
                pd.to_numeric(allparticles[sortcol].iloc[0], downcast="float")
                print("\n----------------------------------------------------------------------")        
                print("\n>> Warning: it looks like this column is numeric but you haven't specified so. Make sure that this is the behavior you intended. Otherwise, use \"column/n\".\n")
                print("----------------------------------------------------------------------")
            except ValueError:
                pass
            print("\n>> Sorted particles by the column " + sortcol + " assuming the column contains text.")
            fileparser.writestar(allparticles.sort_values(by=sortcol), metadata, params["parser_outname"], relegateflag)
        elif inputparams[1] == "s":
            try:
                pd.to_numeric(allparticles[sortcol].iloc[0], downcast="float")
                print("\n----------------------------------------------------------------------")        
                print("\n>> Warning: it looks like this column is numeric but you haven't specified so. Make sure that this is the behavior you intended. Otherwise, use \"column/n\".\n")
                print("----------------------------------------------------------------------")
            except ValueError:
                pass
            print("\n>> Sorted particles by the column " + sortcol + " assuming the column contains text.")
            fileparser.writestar(allparticles.sort_values(by=sortcol), metadata, params["parser_outname"], relegateflag)
        elif inputparams[1] == "n":
            try:
                pd.to_numeric(allparticles[sortcol].iloc[0], downcast="float")
            except ValueError:
                print("\n>> Error: it looks like this column is NOT numeric but you specified that it is.\n")
                sys.exit()
            allparticles[sortcol] = allparticles[sortcol].apply(pd.to_numeric)
            print("\n>> Sorted particles by the column " + sortcol + " assuming the column contains numeric values.")
            fileparser.writestar(allparticles.sort_values(by=sortcol), metadata, params["parser_outname"], relegateflag)
        else:
            print("\n>> Error: use \"n\" after the slash to specify that it is numeric.\n")
        sys.exit()

    #######################################################################
    
    #setup SUBSET for remaining functions if necessary
    
    if relegateflag and not params["parser_optless"]:
        if "_rlnOpticsGroup" in allparticles.columns:
                newparticles, metadata = columnplay.delcolumn(allparticles, ["_rlnOpticsGroup"], metadata)
                metadata[0] = ["#","version","30000"]
                print("\n>> Removed the _rlnOpticsGroup column and Optics table.")
                particles2use = particleplay.checksubset(newparticles, queryexact)
        else:
            particles2use = particleplay.checksubset(allparticles, queryexact)
    else:      
        particles2use = particleplay.checksubset(allparticles, queryexact)
    
    if params["parser_uniquemics"]:
        if not "_rlnMicrographName" in allparticles.columns:
            print("\n>> Error: _rlnMicroraphName does not exist in the star file.\n")
            sys.exit()
        totalmics = len(particles2use["_rlnMicrographName"].unique())
        print("\n>> There are " + str(totalmics) + " unique micrographs in this dataset.\n")
        sys.exit()

    if params["parser_extractparticles"]:
        if params["parser_column"] == "" or params["parser_query"] == "":
            print("\n>> Error: enter a column (--c) and query (--q) to extract.\n")
            sys.exit()
        fileparser.writestar(particles2use, metadata, params["parser_outname"], relegateflag)
        sys.exit()
        
    if params["parser_plot"] != "":
        columntoplot = params["parser_plot"]
        if columntoplot not in particles2use:
            print("\n>> Error: the column \"" + columntoplot + "\" does not exist.\n")
            sys.exit()
        try:
            plots.plotcol(particles2use, columntoplot, outtype)
        except ValueError:
            print("\n>> Error: could not plot the column \"" + columntoplot + "\", maybe it's not numeric.\n")
            sys.exit()
        sys.exit()

    if params["parser_plotangledist"]:
        if "_rlnAngleRot" not in particles2use or "_rlnAngleTilt" not in particles2use:
            print("\n>> Error: the column _rlnAngleRot or _rlnAngleTilt does not exist.\n")
            sys.exit()
        print("\n>> Plotting the particle orientations based on the _rlnAngleRot and _rlnAngleTilt on a Mollweide projection.")
        plots.plotangledist(particles2use, outtype)
        sys.exit()
        
    if params["parser_writecol"] != "": 
        colstowrite = params["parser_writecol"].split("/")
        for col in colstowrite:
            if col not in particles2use:
                print("\n>> Error: the column \"" + str(col) + "\" does not exist in your star file.\n")
                sys.exit()
        outputs = columnplay.writecol(particles2use, colstowrite)
        print("\n>> Wrote entries from " + str(colstowrite) + "\n-->> Output files: " + str(outputs) + " \n")
        sys.exit()
        
    if params["parser_regroup"] != 0:
        numpergroup = params["parser_regroup"]
        regroupedparticles, numgroups = particleplay.regroup(particles2use, numpergroup)
        print("\n>> Regrouped: " + str(numpergroup) + " particles per group with similar defocus values (" + str(numgroups) + " groups in total).")
        fileparser.writestar(regroupedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    #This has to be at the end so it only runs if it is the only passed argument.
    if relegateflag and not params["parser_optless"]:
        fileparser.writestar(particles2use, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    print("\n>> Error: either the options weren't passed correctly or none were passed at all. See the help page (-h).\n")
