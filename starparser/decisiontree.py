import sys
import os.path
import pandas as pd
import matplotlib.pyplot as plt

from starparser import argparser
from starparser import columnplay
from starparser import fileparser
from starparser import particleplay
from starparser import plots
from starparser import specialparticles
from starparser import splits

def decide():

    ##################################
    """
    This is the master function that is used to determine what the user is asking for from the command-line arguments,
    and set up the variables required to call those functions
    """
    ##################################

    #Get the passed parameters
    params = argparser.argparse()

    """
    First, some basic checks
    """

    #The --i option must be passed, otherwise there is nothing to parse.    
    if 'file' not in params:
        print("\n>> Error: no filename entered. See the help page (-h).\n")
        sys.exit()

    #Modify column name to be _rlnXXX regardless of the format input by the user (rln, _rln or no prefix)
    if params["parser_column"] != "":
        tempsplit = params["parser_column"].split("/")
        for i,c in enumerate(tempsplit):
            tempsplit[i] = makefullname(c)
        params["parser_column"]='/'.join(tempsplit)

    print(params["parser_column"])
        
    #This is a rare ocurance, but it's possible that the user asks to delete the _rlnOpticsGroup column as well as pass the --relegate option, which is redundant.
    if "_rlnOpticsGroup" in params["parser_column"] and params["parser_relegate"]:
        print("\n>> Error: cannot have the relegate option and the delete OpticsGroup column at the same time (the former will do the latter already).\n")
        sys.exit()

    #The output file types (--t) for plots are listed below, so any other file type will not work.
    if params["parser_outtype"] not in ["png", "pdf", "jpg", "svg"]:
        print("\n>> Error: choose between png, pdf, svg, and jpg for the plot filetype.\n")
        sys.exit()
        
    ##################################
    """
    The variables below are essential for all functions
    """
    ##################################

    #The name of the star file
    filename = params['file']

    #Check if a star file has been passed. This check is probably redundant with the check above. Consider removing.
    if params['file'] == "":
        print("\n>> Error: enter a star file with --i.\n")
        sys.exit();

    #Check if the file exists
    if not os.path.isfile(filename):
        print("\n>> Error: \"" + filename + "\" does not exist.\n")
        sys.exit();

    #Assign the plot file type to outtype. This is probably not necessary. Consider removing.
    outtype = params["parser_outtype"]

    #The queryexact option checks if the query should match exactly (as opposed to finding any instance of the query).
    queryexact = params["parser_exact"]

    #Assure the user that they have asked for exact values.
    if queryexact:
        print("\n>> You have asked for exact matches between the queries and values (--e).")

    #In the cases below, a subset of particles are generated from a qurey that must be exact, so the queryexact variable is forced to be True.
    elif params["parser_splitoptics"] or params["parser_classiterations"] or params["parser_splitclasses"]:
        queryexact = True

    ##################################
    """
    From here on out, the passed arguments
    are checked and the proper functions are called.
    """
    ##################################
    
    """
    --plot_class_iterations is checked first since the plotclassparts() function can be called
    without having to have read in the star file or check for queries.
    """
    
    if params["parser_classiterations"] != "":
        if params["parser_classiterations"] in ["all", "All", "ALL"]:
            plots.plotclassparts(filename, [-1], queryexact, outtype)
        else:
            plots.plotclassparts(filename,params["parser_classiterations"].split("/"), queryexact, outtype)
        sys.exit()
    

    """
    For most functions, the star file is parsed and basic variables are set before
    deciding which function to call.
    """

    print("\n>> Reading " + filename)

    #The --opticsless option requires the getparticles_dummyoptics function to insert
    #a fake optics table before moving on
    if params["parser_optless"]:

        allparticles, metadata = fileparser.getparticles_dummyoptics(filename)

    ####
    #Most of the time, particles will be parsed normally below
    #The allparticles dataframe will be used in all main functions below
    else:
        allparticles, metadata = fileparser.getparticles(filename)
    ####


    ##########
    """
    Optics based querying here before assuming it is particle based querying
    """

    """
    --extract_optics
    """

    if params["parser_extractoptics"]:
        if params["parser_column"] == "" or params["parser_query"] == "":
            print("\n>> Error: enter a column (--c) and query (--q) to extract.\n")
            sys.exit()
        particles_extractedoptics, newmetadata, extractednumber = particleplay.extractoptics(allparticles, metadata, queryexact)
        print(f"\n>> Extracted {extractednumber} out of {len(allparticles.index)} ({round(100*extractednumber/len(allparticles.index),1)}%) that matched the optics query.")
        fileparser.writestar(particles_extractedoptics, newmetadata, params["parser_outname"], False)
        sys.exit()

    ##########

    #Check how many particles there are. This variable isn't useful yet but will be used for
    #various things later.
    totalparticles = len(allparticles.index)
    
    #If a query was passed, then turn it into a list. Since queries are split by a slash, .split("/") creates the list for us
    #Escape a / with a , preceding it (i.e. ,/).
    #!!This needs to be updated in particleplay if change here!!
    if params["parser_query"] != "":
        query = params["parser_query"]
        escape = ",/"
        query = str.replace(params["parser_query"],escape, ",")
        query = query.split("/")
        for i,q in enumerate(query):
            query[i] = str.replace(q,",", "/")

        #If no column was passed, the query can't be checked.
        if params["parser_column"] == "":
            print("\n>> Error: pass a column with --c for the query to be checked.\n")
            sys.exit()
    
    #Same thing if a column was passed
    if params["parser_column"] != "":
        columns = params["parser_column"].split("/")
        
        #For every column passed, check that it exists as a header in the allparticles dataframe
        for c in columns:
            if c not in allparticles.columns:
                print("\n>> Error: the column [" + str(c) + "] does not exist in your star file.\n")
                sys.exit()
    
    #If not columns were passed, set the variable columns to an empty string,
    #otherwise some functions may throw an error.
    else:    
        columns = ""

    #If the input star file lacks an optics table and the --opticsless option was passed, then
    #it makes sense to output a star file without an optics table too, hence setting relegateflag=True
    if params["parser_optless"]:
        relegateflag = True

    #Otherwise, see what the user requested (i.e. relegateflag will be True if --relegate was passed)    
    else:
        relegateflag = params["parser_relegate"]
    

    ##################################
    """
    Below is a flurry of functions, in no particular order
    """
    ##################################

    """
    --count
    """

    if params["parser_countme"] and params["parser_column"] != "" and params["parser_query"] != "":
        particleplay.countqueryparticles(allparticles, columns, query, queryexact, False)
        sys.exit()
    elif params["parser_countme"]:
        print('\n>> There are ' + str(totalparticles) + ' particles in total.\n') 
        sys.exit()
    
    """
    --remove_column
    """

    if params["parser_delcolumn"] != "":
        columns = makefullname(params["parser_delcolumn"]).split("/")
        for i,c in enumerate(columns):
            columns[i] = makefullname(c)
        newparticles, metadata = columnplay.delcolumn(allparticles, columns, metadata)
        print("\n>> Removed the columns " + str(columns))
        fileparser.writestar(newparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --remove_particles
    """

    if params["parser_delparticles"]:
        if params["parser_query"] == "" or params["parser_column"] == "":
            print("\n>> Error: provide a column (--c) and query (--q) to find specific particles to remove.\n")
            sys.exit()
        newparticles = particleplay.delparticles(allparticles, columns, query, queryexact)
        purgednumber = totalparticles - len(newparticles.index)
        print("\n>> Removed " + str(purgednumber) + " particles (out of " + str(totalparticles) + ", " + str(round(purgednumber*100/totalparticles,1)) + "%) that matched " + str(query) + " in the column " + params["parser_column"] + ".")
        fileparser.writestar(newparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --remove_duplicates
    """

    if params["parser_delduplicates"] != "":
        column = makefullname(params["parser_delduplicates"])
        if column not in allparticles:
            print("\n>> Error: the column " + str(column) + " does not exist in your star file.\n")
            sys.exit()
        newparticles = particleplay.delduplicates(allparticles, column)
        purgednumber = totalparticles - len(newparticles.index)
        newtotal = len(newparticles.index)
        print("\n>> Removed " + str(purgednumber) + " particles (out of " + str(totalparticles) + ", " + str(round(purgednumber*100/totalparticles,1)) + "%) that were duplicates based on the " + column + " column.")
        print(">> The new total is " + str(newtotal) + " particles.")
        fileparser.writestar(newparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --remove_mics_list
    """

    if params["parser_delmics"]:
        if params["parser_query"] != "" or params["parser_column"] != "":
            print("\n>> Error: you cannot provide a query to the --remove_mics_fromlist option.\n")
            sys.exit()
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to match micrographs.\n")
            sys.exit()
        file2 = params["parser_file2"]
        if not os.path.isfile(file2):
            print("\n>> Error: \"" + file2 + "\" does not exist.\n")
            sys.exit()
        with open(file2) as f:
            micstodelete = [line.split()[0] for line in f]
        newparticles = particleplay.delmics(allparticles,micstodelete)
        purgednumber = totalparticles - len(newparticles.index)
        print("\n>> Removed " + str(purgednumber) + " particles (out of " + str(totalparticles) + ", " + str(round(purgednumber*100/totalparticles,1)) + "%) that matched the micrographs in " + file2 + ".")
        fileparser.writestar(newparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --keep_mics_list
    """

    if params["parser_keepmics"]:
        if params["parser_query"] != "" or params["parser_column"] != "":
            print("\n>> Error: you cannot provide a query to the --keep_mics_fromlist option.\n")
            sys.exit()
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to match micrographs.\n")
            sys.exit()
        file2 = params["parser_file2"]
        if not os.path.isfile(file2):
            print("\n>> Error: \"" + file2 + "\" does not exist.\n")
            sys.exit()
        with open(file2) as f:
            micstokeep = [line.split()[0] for line in f]
        newparticles = particleplay.keepmics(allparticles,micstokeep)
        keptnumber = len(newparticles.index)
        print("\n>> Kept " + str(keptnumber) + " particles (out of " + str(totalparticles) + ", " + str(round(keptnumber*100/totalparticles,1)) + "%) that matched the micrographs in " + file2 + ".")
        fileparser.writestar(newparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()
        
    """
    --swap_columns
    """

    if params["parser_swapcolumns"] != "":
        columnstoswap = params["parser_swapcolumns"].split("/")
        for i,c in enumerate(columnstoswap):
            columnstoswap[i]=makefullname(c)
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to swap columns from.\n")
            sys.exit()
        file2 = params["parser_file2"]
        if not os.path.isfile(file2):
            print("\n>> Error: \"" + file2 + "\" does not exist.\n")
            sys.exit();
        print("\n>> Reading " + file2)
        otherparticles, metadata2 = fileparser.getparticles(file2)
        swappedparticles = columnplay.swapcolumns(allparticles, otherparticles, columnstoswap)
        print("\n>> Swapped in " + str(columnstoswap) + " from " + file2)
        fileparser.writestar(swappedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --import_mic_values
    """

    if params["parser_importmicvalues"] != "":
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to import values from.\n")
            sys.exit()
        file2 = params["parser_file2"]
        if not os.path.isfile(file2):
            print("\n>> Error: \"" + file2 + "\" does not exist.\n")
            sys.exit();
        print("\n>> Reading " + file2)
        otherparticles, metadata2 = fileparser.getparticles(file2)
        columnstoimport = params["parser_importmicvalues"].split("/")
        for i,c in enumerate(columnstoimport):
            columnstoimport[i]=makefullname(c)

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

        """
        It is inefficient to update the dataframe one column at a time
        instead of doing them all at the same time. Consider revising.
        """
        importedparticles = allparticles.copy()
        for column in columnstoimport:
            importedparticles = particleplay.importmicvalues(importedparticles, otherparticles, column)

        fileparser.writestar(importedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --expand_optics
    """

    if params["parser_expandoptics"] != "":
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to import values from.\n")
            sys.exit()       
        opticsgrouptoexpand = params["parser_expandoptics"]

        if opticsgrouptoexpand not in metadata[2]["_rlnOpticsGroupName"].tolist():
            print("\n>> Error: the optics group " + opticsgrouptoexpand + " does not exist in the star file.\n")
            sys.exit()

        file2 = params["parser_file2"]
        if not os.path.isfile(file2):
            print("\n>> Error: \"" + file2 + "\" does not exist.\n")
            sys.exit();
        print("\n>> Reading " + file2)
        newdata, newdata_metadata = fileparser.getparticles(file2)

        print("\n>> Expanding the optics group " + opticsgrouptoexpand + " based on the micrograph optics in " + file2)
        
        expandedparticles, newmetadata = particleplay.expandoptics(allparticles,metadata,newdata,newdata_metadata,opticsgrouptoexpand)

        fileparser.writestar(expandedparticles, newmetadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --import_particle_values
    """

    if params["parser_importpartvalues"] != "":
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to import values from.\n")
            sys.exit()
        file2 = params["parser_file2"]
        if not os.path.isfile(file2):
            print("\n>> Error: \"" + file2 + "\" does not exist.\n")
            sys.exit();
        print("\n>> Reading " + file2)
        otherparticles, metadata2 = fileparser.getparticles(file2)
        columnstoimport = params["parser_importpartvalues"].split("/")
        for i,c in enumerate(columnstoimport):
            columnstoimport[i] = makefullname(c)

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

    """
    --operate
    """

    if params["parser_operate"] != "":

        #Check which operation is required by splitting, if the result is 2, then that was the operation
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
        column = makefullname(column)
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

    """
    --operate_columns
    """

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
        column1 = makefullname(column1)

        try:
            column2 = secondhalf.split("=")[0]
            column2 = makefullname(column2)
            newcolumn = secondhalf.split("=")[1]
            newcolumn = makefullname(newcolumn)
        except IndexError:
            print("\n>> Error: the argument to pass is column1[operator]column2=newcolumn (e.g. CoordinateX*OriginX=Shifted). Try using quotations around it if it doesn't work\n")
            sys.exit()

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

    """
    --find_shared
    """
        
    if params["parser_findshared"] != "":
        columntocheckunique = makefullname(params["parser_findshared"])
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
        print("\n>> Reading " + file2)
        otherparticles, f2metadata = fileparser.getparticles(file2)
        unsharedparticles = allparticles[~allparticles[columntocheckunique].isin(otherparticles[columntocheckunique])]
        sharedparticles = allparticles[allparticles[columntocheckunique].isin(otherparticles[columntocheckunique])]
        
        print("\nShared: \n-------\n" + str(len(sharedparticles.index)) + " particles are shared between " + filename + " and " + file2 + " in the " + str(columntocheckunique) + " column.\n")
        fileparser.writestar(sharedparticles, metadata, "shared.star", relegateflag)
        print("Unique: \n-------\n·" + filename + ": " + str(len(unsharedparticles.index)) + " particles (written to unique.star if non-zero)\n·" + file2 + ": " + str(len(otherparticles.index) - len(sharedparticles.index)) + " particles\n")
        if not unsharedparticles.empty:
            fileparser.writestar(unsharedparticles, metadata, "unique.star", relegateflag)

        sys.exit()


    """
    --match_mics
    """
        
    if params["parser_matchmics"]:
        columntocheckunique = params["parser_findshared"]
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to compare to.\n")
            sys.exit()
        file2 = params["parser_file2"]
        if not os.path.isfile(file2):
            print("\n>> Error: \"" + file2 + "\" does not exist.\n")
            sys.exit();
        print("\n>> Reading " + file2)
        otherparticles, f2metadata = fileparser.getparticles(file2)
        matchedparticles = allparticles[allparticles["_rlnMicrographName"].isin(otherparticles["_rlnMicrographName"])]
        print("\n>> Kept " + str(len(set(matchedparticles["_rlnMicrographName"].tolist()))) + " micrographs that matched the second file (out of " + str(len(set(allparticles["_rlnMicrographName"].tolist()))) + ").\n")
        fileparser.writestar(matchedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --extract_if_nearby
    """

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

        print("\n>> Reading " + params["parser_file2"])
        nearparticles, nearmetadata = fileparser.getparticles(params["parser_file2"])

        print("\n>> Creating subsets with particles that are closer/further than " + str(threshdist) + " pixels from the closest particle in the second star file.")

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

    """
    --fetch_from_nearby
    """

    if params["parser_fetchnearby"] != "":
        retrieveparams = params["parser_fetchnearby"].split("/")
        if len(retrieveparams) < 2:
            print("\n>> Error: provide argument in this format: distance/column(s) (e.g. 300/_rlnClassNumber).")
            sys.exit()
        columnstoretrieve = retrieveparams[1:]
        for i,c in enumerate(columnstoretrieve):
            columnstoretrieve[i]=makefullname(c)
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
        print("\n>> Reading " + params["parser_file2"])
        nearparticles, nearmetadata = fileparser.getparticles(params["parser_file2"])
        for c in columnstoretrieve:
            if c not in nearparticles:
                print("\n>> Error: " + c + " does not exist in the second star file.\n")
                sys.exit()
        print("\n>> Fetching " + str(columnstoretrieve) + " values from particles within " + str(threshdist) + " pixels.\n")
        stolenparticles = specialparticles.fetchnearby(allparticles, nearparticles, threshdist, columnstoretrieve)
        fileparser.writestar(stolenparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --extract_cluster
    """

    if params["parser_cluster"] != "":
        retrieveparams = params["parser_cluster"].split("/")
        if len(retrieveparams) != 2:
            print("\n>> Error: provide argument in this format: threshold-distance/minimum-per-cluster (e.g. 400/4).")
            sys.exit()
        threshold = float(retrieveparams[0])
        minimum = int(retrieveparams[1])
        print("\n>> Extracting particles that have at least " + str(minimum) + " neighbors within " + str(threshold) + " pixels.\n")
        clusterparticles = specialparticles.getcluster(allparticles, threshold,minimum)
        print(">> Removed " + str(len(allparticles.index)-len(clusterparticles.index)) + " that did not match the criteria (" + str(len(clusterparticles.index)) + " remaining out of " + str(len(allparticles.index)) + ").")
        fileparser.writestar(clusterparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()


    """
    --extract_min
    """

    if params["parser_exractmin"] != -1:
        extractmin = params["parser_exractmin"]
        print("\n>> Extracting particles that belong to micrographs with at least " + str(extractmin) + " particles.\n")
        particlesfrommin = specialparticles.extractwithmin(allparticles, extractmin)
        print(">> Removed " + str(len(allparticles.index)-len(particlesfrommin.index)) + " that did not match the criteria (" + str(len(particlesfrommin.index)) + " remaining out of " + str(len(allparticles.index)) + ").")
        fileparser.writestar(particlesfrommin, metadata, params["parser_outname"], relegateflag)
        sys.exit()



    """
    --plot_class_proportions
    """
        
    if params["parser_classproportion"]:
        if params["parser_query"] == "":
            print("\n>> Error: you have not entered a query.\n")
            sys.exit()
        elif params["parser_column"] == "":
            print("\n>> Error: you have not entered a column.\n")
            sys.exit()
        plots.classproportion(allparticles, columns, query, queryexact, outtype)
        sys.exit()
        
    """
    --new_optics
    """
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

    """
    --limit
    """

    if params["parser_limitparticles"] != "":
        parsedinput = params["parser_limitparticles"].split("/")
        if len(parsedinput) != 3:
            print("\n>> Error: provide argument in this format: column/operator/value (e.g. _rlnDefocusU/lt/40000).\n")
            sys.exit()
        columntocheck = makefullname(parsedinput[0])
        operator = parsedinput[1]
        limit = float(parsedinput[2])
        if operator not in ["lt", "gt", "le", "ge"]:
            print("\n>> Error: use \"lt\" (less than), \"gt\" (greater than), \"le\" (less than or equal to), or \"ge\" (greater than or equal to) as the operator.\n")
            sys.exit()
        limitedparticles = particleplay.limitparticles(allparticles, columntocheck, limit, operator)
        if operator == "lt":
            print("\n>> Extracted " + str(len(limitedparticles.index)) + " particles (out of " + str(totalparticles) + ", " + str(round(len(limitedparticles.index)*100/totalparticles,1)) + "%) that have " + str(columntocheck) + " values less than " + str(limit))
        elif operator == "gt":
            print("\n>> Extracted " + str(len(limitedparticles.index)) + " particles (out of " + str(totalparticles) + ", " + str(round(len(limitedparticles.index)*100/totalparticles,1)) + "%) that have " + str(columntocheck) + " values greater than " + str(limit))
        elif operator == "le":
            print("\n>> Extracted " + str(len(limitedparticles.index)) + " particles (out of " + str(totalparticles) + ", " + str(round(len(limitedparticles.index)*100/totalparticles,1)) + "%) that have " + str(columntocheck) + " values less than or equal to " + str(limit))
        elif operator == "ge":
            print("\n>> Extracted " + str(len(limitedparticles.index)) + " particles (out of " + str(totalparticles) + ", " + str(round(len(limitedparticles.index)*100/totalparticles,1)) + "%) that have " + str(columntocheck) + " values greater than or equal to " + str(limit))
        fileparser.writestar(limitedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --extract_random
    """

    if params["parser_randomset"] != -1:
        numrandom = params["parser_randomset"]
        if numrandom == 0:
            print("\n>> Error: you cannot pass 0 particles.\n")
        if numrandom > totalparticles:
            print("\n>> Error: the number of particles you want to randomly extract cannot be greater than the total number of particles (" + str(totalparticles) + ").\n")
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

    """
    --split
    """

    if params["parser_split"] != -1:
        numsplits = params["parser_split"]
        if numsplits == 1:
            print("\n>> Error: you cannot split into 1 part.\n")
            sys.exit()
        if numsplits > totalparticles:
            print("\n>> Error: you cannot split into more parts than there are particles.\n")
            sys.exit()
        splitstars = splits.splitparts(allparticles,numsplits)
        print("\n")
        fill = len(str(len(splitstars)))
        for i,s in enumerate(splitstars):
            print(">> There are " + str(len(s.index)) + " particles in file " + str(i+1))
            fileparser.writestar(s, metadata, filename[:-5]+"_split-"+str(i+1).zfill(fill)+".star", relegateflag)
        sys.exit()

    """
    --split_optics
    """

    if params["parser_splitoptics"]:
        splits.splitbyoptics(allparticles,metadata,queryexact)
        sys.exit()

    """
    --split_classes
    """

    if params["parser_splitclasses"]:
        if "_rlnClassNumber" not in allparticles:
            print("\n>> Error: _rlnClassNumber does not exist in the star file.")
        splits.splitbyclass(allparticles,metadata,queryexact,relegateflag)
        sys.exit()

    """
    --extract_indices
    """

    if params["parser_getindex"]:
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f that has the list of values.\n")
            sys.exit()
        with open(params["parser_file2"]) as f:
            indicestoget = [line.split()[0] for line in f]
        indicestoget = [(int(i)-1) for i in indicestoget]
        if max(indicestoget)+1 > totalparticles:
            print("\n>> Error: the index " + str(max(indicestoget)+1) + " is out of bounds (the last index in your star file is " + str(totalparticles) + ").\n")
            sys.exit()
        print("\n>> Extracting " + str(len(indicestoget)) + " particles (" + str(round(100*len(indicestoget)/totalparticles,1)) + "%) that match the indices.")
        fileparser.writestar(allparticles.iloc[indicestoget], metadata, params["parser_outname"], relegateflag)
        sys.exit()   

    """
    --insert_column
    """

    if params["parser_insertcol"] != "":
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f that has the list of values.\n")
            sys.exit()
        insertcol = makefullname(params["parser_insertcol"])
        if insertcol in allparticles.columns:
            print("\n>> Error: the column " + str(insertcol) + " already exists in your star file. Use --replace_column if you would like to replace it.\n")
            sys.exit()
        newcolfile = params["parser_file2"]
        with open(newcolfile) as f:
            newcolvalues = [line.split()[0] for line in f]
        if len(newcolvalues) != totalparticles:
            print("\n>> Error: your star file has " + str(totalparticles) + " values while your second file has " + str(len(newcolvalues)) + " values.\n")
            sys.exit()
        print("\n>> Creating the column " + insertcol + " with the values in " + newcolfile + ".")
        allparticles[insertcol]=newcolvalues
        metadata[3].append(insertcol)
        fileparser.writestar(allparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --insert_optics_column
    """

    if params["parser_insertopticscol"] != "":
        try:
            new_header, value = params["parser_insertopticscol"].split("/")
        except ValueError:
            print("\n>> Error: the argument to pass is column-name/value.\n")
            sys.exit()
        new_header = makefullname(new_header)
        print("\n Creating the column " + new_header + " in the optics table with the value " + value)

        metadata[2][new_header]=value
        metadata[1].append(new_header)
        fileparser.writestar(allparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --remove_poses
    """

    if params["parser_removeposes"]:
        filtered_particles = particleplay.remove_poses(allparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --plot_coordinates
    """

    if params["parser_comparecoords"] != "":
        if params["parser_file2"] == "":
            file2particles = pd.DataFrame({'A' : []})
        else:
            print("\n>> Reading " + params["parser_file2"])
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
            #This is arbitrary
            circlesize = 200

        if not file2particles.empty:
            if numtoplot != -1:
                print("\n>> Plotting coordinates from the star file (red circles) and second file (blue circles) for " + str(numtoplot) + " micrograph(s).")
            else:
                print("\n>> Plotting coordinates from the star file (red circles) and second file (blue circles) for " + str(len(file1mics)) + " micrograph(s).")
        else:
            if numtoplot != -1:
                print("\n>> Plotting coordinates from the star file (red circles) for " + str(numtoplot) + " micrograph(s).")
            else:
                print("\n>> Plotting coordinates from the star file (red circles) for " + str(len(file1mics)) + " micrograph(s).")

        plots.comparecoords(allparticles, file2particles, numtoplot, circlesize)
        sys.exit()

    """
    --replace_column
    """

    if params["parser_replacecol"] != "":
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f that has the list of values.\n")
            sys.exit()
        replacecol = makefullname(params["parser_replacecol"])
        if replacecol not in allparticles.columns:
            print("\n>> Error: the column " + str(replacecol) + " does not exist in your star file.\n")
            sys.exit()
        newcolfile = params["parser_file2"]
        with open(newcolfile) as f:
            newcol = [line.split()[0] for line in f]
        if len(newcol) != totalparticles:
            print("\n>> Error: your star file has " + str(totalparticles) + " values while your second file has " + str(len(newcol)) + " values.\n")
            sys.exit()
        print("\n>> Replacing values in the column " + replacecol + " with those in " + newcolfile + ".")
        replacedstar = columnplay.replacecolumn(allparticles,replacecol,newcol)
        fileparser.writestar(replacedstar, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --copy_column
    """

    if params["parser_copycol"] != "":

        inputparams = params["parser_copycol"].split("/")
        if len(inputparams) != 2:
            print("\n>> Error: the input should be source-column/target-column.\n")
            sys.exit()
        sourcecol, targetcol = inputparams
        sourcecol = makefullname(sourcecol)
        targetcol = makefullname(targetcol)
        if sourcecol not in allparticles:
            print("\n>> Error: " + sourcecol + " does not exist in the star file.\n")
            sys.exit()
        copiedstar = columnplay.copycolumn(allparticles,sourcecol,targetcol,metadata)
        fileparser.writestar(copiedstar, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --reset_column
    """

    if params["parser_resetcol"] != "":

        inputparams = params["parser_resetcol"].split("/")
        if len(inputparams) != 2:
            print("\n>> Error: the input should be column-name/value.\n")
            sys.exit()
        columntoreset, value = inputparams
        columntoreset = makefullname(columntoreset)
        if columntoreset not in allparticles:
            print("\n>> Error: " + columntoreset + " does not exist in the star file.\n")
            sys.exit()
        resetstar = columnplay.resetcolumn(allparticles,columntoreset,value)
        fileparser.writestar(resetstar, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --sort_by
    """

    if params["parser_sort"] != "":
        inputparams = params["parser_sort"].split("/")
        sortcol = makefullname(inputparams[0])
        if sortcol not in allparticles.columns:
            print("\n>> Error: the column " + str(sortcol) + " does not exist in your star file.\n")
            sys.exit()

        if len(inputparams) == 1:
            try:
                pd.to_numeric(allparticles[sortcol].iloc[0], downcast="float")
                print("\n----------------------------------------------------------------------")        
                print("\n>> Warning: it looks like this column is numeric but you haven't specified so.\n>> Make sure that this is the behavior you intended. Otherwise, use \"column/n\".\n")
                print("----------------------------------------------------------------------")
            except ValueError:
                pass
            print("\n>> Sorted particles by the column " + sortcol + " assuming the column contains text.")
            fileparser.writestar(allparticles.sort_values(by=sortcol), metadata, params["parser_outname"], relegateflag)

        elif inputparams[1] == "s":
            try:
                pd.to_numeric(allparticles[sortcol].iloc[0], downcast="float")
                print("\n----------------------------------------------------------------------")        
                print("\n>> Warning: it looks like this column is numeric but you haven't specified so.\n>> Make sure that this is the behavior you intended. Otherwise, use \"column/n\".\n")
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
            print("\n>> Error: type \"n\" after the slash to specify that it is numeric.\n")

        sys.exit()

    """
    --swap_optics
    """

    if params["parser_swapoptics"]:
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to swap in the optics table from.\n")
            sys.exit()
        file2 = params["parser_file2"]
        if not os.path.isfile(file2):
            print("\n>> Error: \"" + file2 + "\" does not exist.\n")
            sys.exit()
        print("\n>> Reading " + file2)
        otherparticles, newmetadata = fileparser.getparticles(file2)
        fileparser.writestar(allparticles, [metadata[0],newmetadata[1],newmetadata[2],metadata[3],metadata[4]], params["parser_outname"], relegateflag)
        sys.exit()


    ############
    """
    The remaining functions may all be passed with a query (--c/--q)
    to either extract/plot specific particles, or write out a column.
    """
    ############

    """
    Create the subset of particles particles2use from allparticles
    At the moment, checksubset() only takes in the particles and the queryexact variable,
    while the column and queries are re-processed within checksubset(). This is inefficient
    and should be revised.
    checksubset() returns the original particles if no query exists, so sometimes particles2use
    will be equivalent to allparticles
    """

    #Check if the --relegate option was passed and remove the _rlnOpticsGroup column first before
    #generating a subset
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
    
    """
    --extract
    """
    #Particles were already subsetted above, just write them here
    if params["parser_extractparticles"]:
        if params["parser_column"] == "" or params["parser_query"] == "":
            print("\n>> Error: enter a column (--c) and query (--q) to extract.\n")
            sys.exit()
        fileparser.writestar(particles2use, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    """
    --count_mics
    """

    if params["parser_uniquemics"]:
        if not "_rlnMicrographName" in allparticles.columns:
            print("\n>> Error: _rlnMicroraphName does not exist in the star file.\n")
            sys.exit()
        totalmics = len(particles2use["_rlnMicrographName"].unique())
        print("\n>> There are " + str(totalmics) + " unique micrographs in this dataset.\n")
        sys.exit()

    """
    --histogram
    """

    if params["parser_plot"] != "":
        columntoplot = makefullname(params["parser_plot"])
        if columntoplot not in particles2use:
            print("\n>> Error: the column \"" + columntoplot + "\" does not exist.\n")
            sys.exit()
        try:
            plots.plotcol(particles2use, columntoplot, outtype)
        except ValueError:
            print("\n>> Error: could not plot the column \"" + columntoplot + "\", maybe it's not numeric.\n")
            sys.exit()
        sys.exit()

    """
    --plot_orientations
    """

    if params["parser_plotangledist"]:
        if "_rlnAngleRot" not in particles2use or "_rlnAngleTilt" not in particles2use:
            print("\n>> Error: the column _rlnAngleRot or _rlnAngleTilt does not exist.\n")
            sys.exit()
        print("\n>> Plotting the particle orientations based on the _rlnAngleRot and _rlnAngleTilt on a Mollweide projection.")
        plots.plotangledist(particles2use, outtype)
        sys.exit()

    """
    --list_column
    """
        
    if params["parser_writecol"] != "": 
        colstowrite = params["parser_writecol"].split("/")
        for i,col in enumerate(colstowrite):
            col = makefullname(col)
            colstowrite[i] = col
            if col not in particles2use:
                print("\n>> Error: the column \"" + str(col) + "\" does not exist in your star file.\n")
                sys.exit()
        outputs = columnplay.writecol(particles2use, colstowrite)
        print("\n>> Wrote entries from " + str(colstowrite) + "\n-->> Output files: " + str(outputs) + " \n")
        sys.exit()
        
    """
    --regroup
    """

    if params["parser_regroup"] != 0:
        numpergroup = params["parser_regroup"]
        regroupedparticles, numgroups = particleplay.regroup(particles2use, numpergroup)
        print("\n>> Regrouped: " + str(numpergroup) + " particles per group with similar defocus values (" + str(numgroups) + " groups in total).")
        fileparser.writestar(regroupedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()


    """
    If --relegate is the only option that is passed, then the star file is written without the optics table
    and without _rlnOpticsGroup (which was removed above already).
    """

    #This has to be at the end so it only runs if it is the only passed argument.
    if relegateflag and not params["parser_optless"]:
        fileparser.writestar(particles2use, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    #The end.
    print("\n>> Error: either the options weren't passed correctly or none were passed at all. See the help page (-h).\n")


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

