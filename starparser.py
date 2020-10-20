import sys
import pandas as pd
import optparse

def setupParserOptions():
    
    parser = optparse.OptionParser(usage="Usage: %prog [options]",
        version="%prog 1.0.")

    parser.add_option("--i",
        action="store", dest="file",
        help="Input file name.")

    parser.add_option("--plot_defocus",
        action="store_true", dest="parser_plotdefocus", default=False,
        help="Plot defocus to Defocus_histogram.png. Can be used with -c and -q for a subset count, otherwise plots all.")
    
    parser.add_option("--plot_classparts",
        action="store_true", dest="parser_classdistribution", default=False,
        help="Plot the number of particles per class for all iterations up to the one provided in the input.")
    
    parser.add_option("--delete_column",
        action="store", dest="parser_delcolumn", type="string", default="",
        help="Delete column and renumber headers. E.g. _rlnMicrographName. To enter multiple columns, separate them with a slash: _rlnMicrographName/_rlnCoordinateX.")
    
    parser.add_option("--delete_particles",
        action="store_true", dest="parser_delparticles", default=False,
        help="Delete particles. Pick a column header (-c) and query (-q) to delete particles that match it.")
    
    parser.add_option("--extract_particles",
        action="store_true", dest="parser_extractparticles", default=False,
        help="Write a star file with particles that match a column header (-c) and query (-q).")

    parser.add_option("--count_particles",
        action="store_true", dest="parser_countme", default=False,
        help="Count particles and print the result. Can be used with -c and -q for a subset count, otherwise counts all.")
    
    parser.add_option("--count_mics",
        action="store_true", dest="parser_uniquemics", default=False,
        help="Count the number of unique micrographs. Can be used with -c and -q for a subset count, otherwise counts all.")
    
    parser.add_option("--max_defocus",
        action="store", dest="parser_maxdefocus", type="float", default = 0,
        help="Extract particles with defocus values less than this value (Angstroms). Can be used with -c and -q to only consider a subset.")
    
    parser.add_option("--list_column",
        action="store", dest="parser_writecol", type="string", default="",
        help="Write all values of a column to a file (filename is the header). E.g. _rlnMicrographName. To enter multiple columns, separate them with a slash: _rlnMicrographName/_rlnCoordinateX. Can be used with -c and -q for a subset count, otherwise lists all items.")
    
    parser.add_option("-c",
        action="store", dest="parser_column", type="string", default="",
        help="Column query. E.g. _rlnMicrographName. To enter multiple columns, separate them with a slash: _rlnMicrographName/_rlnCoordinateX.")
    
    parser.add_option("-q",
        action="store", dest="parser_query", type="string", default="",
        help="Particle query. To enter multiple columns, separate them with a slash: 20200101/20200203.")
    
    parser.add_option("--swap_columns",
        action="store", dest="parser_swapcolumns", type="string", default="",
        help="Swap columns from another star file (specified with -f). E.g. _rlnMicrographName. To enter multiple columns, separate them with a slash: _rlnMicrographName/_rlnCoordinateX.")

    parser.add_option("--compare_particles",
        action="store", dest="parser_compareparts", type="string", default="",
        help="Count the number of particles that are shared between the input star file and the one provided here. Also counts the number that are unique to each star file.")
    
    
    parser.add_option("--f",
        action="store", dest="parser_file2", default="",
        help="Name of second file to extract columns from.")
    
    parser.add_option("--relegate",
        action="store_true", dest="parser_relegate", default=False,
        help="Remove optics table and optics column. This may not be sufficient to be fully compatible with Relion 3.0. Use --delete_column to remove other bad columns before this, if necessary.")

    parser.add_option("--regroup",
        action="store", dest="parser_regroup", type="int", default=50,
        help="Regroup particles such that those with similar defocus values are in the same group. Any value can be entered. This is useful if there aren't enough particles in each micrograph to make meaningful groups. Note that Subset selection in Relion can also regroup.")
    
    parser.add_option("--o",
        action="store", dest="parser_output", default = "output.star",
        help="Output file name. Default is output.star")

    options,args = parser.parse_args()

#    #for when the filename was an argument without option
#     if len(args) > 1:
#             parser.error("\nToo many filenames.")
#     if len(args) == 0:
#             parser.error("\nNo filename. Run  %prog -h to get the help text.")
#     if len(sys.argv) < 2:
#             parser.print_help()
#             sys.exit()

    if len(sys.argv) < 4:
            parser.print_help()
            sys.exit()

    params={}

    for i in parser.option_list:
            if isinstance(i.dest,str):
                    params[i.dest] = getattr(options,i.dest)
                    
#     params['file'] = args[0] #for when the filename was an argument without option
                    
    return(params)

def parsestar(starfile):

    starfilesplit = starfile.split()

    version = starfilesplit[0:3]

    opticsstop = 0

    for i in range(4,100):
        
        if starfilesplit[i] == '#':
            
            opticsstop = i
            
            break
            
    if opticsstop == 0:
        
        print('Could not find end of optics table. Exiting.')
        
        sys.exit()

    particlesstop = 0
            
    for i in range(opticsstop+3,200):

        if starfilesplit[i].replace('.','',1).replace('-','',1).isnumeric() or ".mrc" in starfilesplit[i]:
            
            particlesstop = i
            
            break

    if particlesstop == 0:

        print('Could not find end of particles table. Exiting.')

        sys.exit()

    opticstable = starfilesplit[3:opticsstop]

    particlestable = starfilesplit[opticsstop+3:particlesstop]
    
    headers = []
    for m in particlestable[::2][1:]: 
        headers.append(m)

    particles = starfilesplit[particlesstop:]

    return(version,opticstable,headers,particles)

#######################################################################################################

def getparticles(filename):
    
    file = open(filename,mode='r')
    starfile = file.read()
    file.close()

    version, opticstable, headers, particles = parsestar(starfile)
    
    metadata = [version,opticstable,headers]

    totalcolumns = len(headers)

    particles_lst = [particles[x:x+totalcolumns] for x in range(0, len(particles), totalcolumns)]

    allparticles = pd.DataFrame(particles_lst, columns = headers)

    return(allparticles, metadata)

def countparticles(particles):

    totalparticles = len(particles.index)
    print('\nThere are ' + str(totalparticles) + ' particles in total.\n')    

def countqueryparticles(particles,columns,query,quiet):

    totalparticles = len(particles.index)
    
    totalquery = 0
    
    if len(columns)>1:
        print("\nError: you have specified two different columns.\n")
        sys.exit()
    
    q = "|".join(query)
    totalquery += len(particles[particles[columns[0]].str.contains(q)].index)
        
    percentparticles = round(totalquery*100/totalparticles,1)

    if not quiet:
        print('\nThere are ' + str(totalquery) + ' particles that match ' + str(query) + ' in the specified columns (out of ' + str(totalparticles) + ', or ' + str(percentparticles) + '%).\n')

    return(totalquery)
        
def plotdefocus(particles):
    
    particles["_rlnDefocusU"] = pd.to_numeric(particles["_rlnDefocusU"], downcast="float")

    ax = particles["_rlnDefocusU"].plot.hist(bins=400)
    ax.set_xlabel("DefocusU")
    
    fig = ax.get_figure()
    fig.savefig('Defocus_histogram.png')
    
def plotclassparts(filename):
    
    position = filename.find("_it")
    iteration = int(filename[position+3:position+6])
    classdistribution = []
    allparticles, metadata = getparticles(filename)
    numclasses = int(max(allparticles["_rlnClassNumber"]))
    
    print("\nLooping from iteration 0 to " + str(iteration) + " on " + str(numclasses) + " classes.\n")

    numperclassdf = pd.DataFrame()

    for i in range(iteration+1):
        iterationstring = str(i).zfill(3)
        iterationfile = filename[:position+3] + iterationstring + filename[position+6:]
        allparticles, metadata = getparticles(iterationfile)
        numperclass = []
        for c in range(1,numclasses+1):
            numperclass.append(countqueryparticles(allparticles, ["_rlnClassNumber"], [str(c)], True))
        numperclassdf[str(i)] = numperclass

    numperclassdf.index +=1

    for c in range(numclasses):
        ax = numperclassdf.iloc[c].plot(kind='line', legend = True, linewidth = 2, alpha = 0.7)
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Particle number")
    fig = ax.get_figure()
    fig.savefig('Class_distribution.png')
    
def maxdefocus(particles, maxvalue):
    
    particles["_rlnDefocusU_float"] = particles["_rlnDefocusU"]
    particles["_rlnDefocusU_float"] = pd.to_numeric(particles["_rlnDefocusU_float"], downcast="float")
    purgedparticles = particles.copy()
    purgedparticles = purgedparticles[purgedparticles["_rlnDefocusU_float"]<maxvalue]
    
    purgednumber = len(particles.index) - len(purgedparticles.index)
    
    particles.drop("_rlnDefocusU_float",1, inplace=True)
    purgedparticles.drop("_rlnDefocusU_float",1, inplace=True)
    
    return(purgedparticles, purgednumber)

def delcolumn(particles, columns, metadata):
    
    nocolparticles = particles.copy()
    
    for c in columns:
        nocolparticles.drop(c, 1, inplace=True)
        metadata[2].remove(c)
    
    return(nocolparticles, metadata)

def delparticles(particles, columns, query):
    
    purgedparticles = particles.copy()
    
    if len(columns)>1:
        print("Error: you have specified two columns. You can't if you're querying to delete.\n")
        sys.exit()
        
    q = "|".join(query)
    
    purgedparticles.drop(purgedparticles[purgedparticles[columns[0]].str.contains(q)].index , 0,inplace=True)
    
    return(purgedparticles)

def extractparticles(particles, columns, query):

    extractedparticles = particles.copy()
    
    if len(columns)>1:
        print("Error: you have specified two columns. Only specify one if you're extracting from a subset of the data using a query.\n")
        sys.exit()
    
    q = "|".join(query)
    
    extractedparticles.drop(extractedparticles[~extractedparticles[columns[0]].str.contains(q)].index, 0,inplace=True)
    
    extractednumber = len(extractedparticles.index)
    
    return(extractedparticles, extractednumber)

def swapcolumns(original_particles, swapfrom_particles, columns):
    
    swappedparticles = original_particles.copy()
    
    for c in columns:
        columnindex = original_particles.columns.get_loc(c)
        swappedparticles.drop(c,1, inplace=True)
        swappedparticles.insert(columnindex, c, swapfrom_particles[c].values.tolist())
    
    return(swappedparticles)

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

def writestar(particles, metadata, outputname, relegate):
    
    output = open(outputname,"w")
    
    output.write('\n')

    version = metadata[0]

    for t in version:
        output.write(t)
        output.write(' ')
    output.write('\n\n')
    
    if not relegate:

        output.write('data_optics\n\n')
        output.write('loop_\n')

        opticstable = metadata[1][1:]

        for n,i in enumerate(opticstable[1:]):

            output.write(i)
            output.write('\t')
            if i[0] != '#':
                if i[0] != '_':
                    opticsvaluesstart=n+2
                    break
            else:
                output.write("\n")

        for i in opticstable[opticsvaluesstart:]:
            output.write(i)
            output.write('\t')
        output.write('\n\n\n')

        for t in version:
            output.write(t)
            output.write(' ')
        output.write('\n\n')

    output.write('data_particles\n\n')
    output.write('loop_')

    headers = metadata[2]
    count=1
    for p in headers:
        output.write('\n')
        output.write(p)
        output.write(" #"+str(count))
        count += 1

    output.write('\n')
    particles.to_csv(output, header=None, index=None, sep=' ', mode='a')

    output.close()
    
def checksubset(particles, params):
    
    if params["parser_column"] != "" and params["parser_query"] != "":
        query = params["parser_query"].split("/")
        columns = params["parser_column"].split("/")
        subsetparticles, extractednumber = extractparticles(particles, columns, query)
        
        print("\nCreating a subset of " + str(extractednumber) + " particles that match " + str(query) +               " in the columns " + str(columns) + " (or " + str(round(extractednumber*100/len(particles.index),1)) + "%)")
        
        return(subsetparticles)
    
    else:
        return(particles)
    
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

def regroup(particles, numpergroup):
    
    newgroups = []
    roundtotal = round(len(particles.index)/numpergroup)
    leftover = (len(particles.index)) % numpergroup
    for i in range(roundtotal):
        newgroups.append([i for j in range(numpergroup)])
    newgroups.append([newgroups[-1][-1] for i in range(leftover)])
    newgroups = [item for sublist in newgroups for item in sublist]

    regroupedparticles = particles.copy()
    regroupedparticles.sort_values("_rlnDefocusU", inplace=True)
    regroupedparticles.drop("_rlnGroupNumber", 1, inplace=True)
    regroupedparticles["_rlnGroupNumber"] = newgroups
    regroupedparticles.sort_index(inplace = True)
    regroupedparticles = regroupedparticles[particles.columns]

    return(regroupedparticles)
    
########################################################
    
def mainloop(params):
    
    ##############################################################
    
    #CHECKS
    
    if 'file' not in params:
        print("Error: no filename entered. See documentation with starparse.py -h.")
        sys.exit()
        
    if "_rlnOpticsGroup" in params["parser_column"] and params["parser_relegate"]:
        print("Error: cannot have the relegate option and the delete OpticsGroup column at the same time (the former will do the latter already).")
        sys.exit()
        
        
    ################################################################
    
    #Essential variables
    
    filename = params['file']
    
    #####################################################################
    
    #Set up jobs that don't require initialization
    
    if params["parser_classdistribution"]:
        plotclassparts(filename)
        print("\n-->Output to Class_distribution.png.\n")
        sys.exit()
    
    #########################################################################
    
    #Initialize stuff
    
    allparticles, metadata = getparticles(filename)

    totalparticles = len(allparticles.index)
    
    if params["parser_query"] != "":
        query = params["parser_query"].split("/")
    
    if params["parser_column"] != "":
        columns = params["parser_column"].split("/")
        
        for c in columns:
            if c not in allparticles.columns:
                print("Error: the column [" + str(c) + "] does not exist in your star file.")
                sys.exit()
                
    else:
        
        columns = ""
        
    relegateflag = params["parser_relegate"]
    
    #####################################################################
        
    #Set up jobs that don't require a subset (faster this way)
    
    if params["parser_countme"] and params["parser_column"] != "" and params["parser_query"] != "":
        countqueryparticles(allparticles, columns, query, False)
        sys.exit()
    elif params["parser_countme"]:
        countparticles(allparticles)
        sys.exit()
        
    if params["parser_delcolumn"] != "":
        columns = params["parser_delcolumn"].split("/")
        newparticles, metadata = delcolumn(allparticles, columns, metadata)
        writestar(newparticles, metadata, params["parser_output"], relegateflag)
        print("\nRemoved the columns " + str(columns) + "\nOutput star file: " + params["parser_output"] + "\n")
        sys.exit()
        
    if params["parser_delparticles"]:
        newparticles = delparticles(allparticles, columns, query)
        purgednumber = len(allparticles.index) - len(newparticles.index)
        writestar(newparticles, metadata, params["parser_output"], relegateflag)
        print("\nRemoved " + str(purgednumber) + " particles out of " + str(totalparticles) + " that had particles that matched " + str(query) +               " in the column " + params["parser_column"] + " (or " + str(round(purgednumber*100/totalparticles,1)) + "%).\n-->Output star file: " + params["parser_output"] + "\n")
        sys.exit()
        
    if params["parser_swapcolumns"] != "":
        if params["parser_file2"] == "":
            print("Error: provide a second file to swap columns from with -f.")
            sys.exit()
        otherparticles, metadata = getparticles(params["parser_file2"])
        columstoswap = params["parser_swapcolumns"].split("/")
        swappedparticles = swapcolumns(allparticles, otherparticles, columstoswap)
        writestar(swappedparticles, metadata, params["parser_output"], relegateflag)
        print("\nSwapped in " + str(columstoswap) + " from " + params["parser_file2"] +               "\n-->Output star file: " + params["parser_output"] + "\n")
        sys.exit()
        
    if params["parser_compareparts"] != "":
        otherparticles, metadata = getparticles(params["parser_compareparts"])
        sharedparticles = len(set(allparticles["_rlnImageName"]) & set(otherparticles["_rlnImageName"]))
        unsharedfile1 = len(allparticles["_rlnImageName"]) - sharedparticles
        unsharedfile2 = len(otherparticles["_rlnImageName"]) - sharedparticles
        print("\n" + filename + " and " + params["parser_compareparts"] + " share " + str(sharedparticles) + " particles.")
        print(filename + " has " + str(unsharedfile1) + " unique particles and " + params["parser_compareparts"] + " has " + str(unsharedfile2) + " unique particles.\n")
    
    #######################################################################
    
    #setup SUBSET for remaining functions if necessary
    
    if relegateflag:
        newparticles, metadata = delcolumn(allparticles, ["_rlnOpticsGroup"], metadata)
        particles2use = checksubset(newparticles, params)
    else:      
        particles2use = checksubset(allparticles, params)
    
    if params["parser_uniquemics"]:
        totalmics = len(particles2use["_rlnMicrographName"].unique())
        print("\nThere are " + str(totalmics) + " unique micrographs in this dataset.\n")
        sys.exit()

    if params["parser_extractparticles"]:
        writestar(particles2use, metadata, params["parser_output"], relegateflag)
        print("\n-->Output star file: " + params["parser_output"] + "\n")
        sys.exit()
        
    if params["parser_plotdefocus"]:
        plotdefocus(particles2use)
        print("\n-->Output to Defocus_histogram.png.\n")
        sys.exit()
        
    if params["parser_maxdefocus"] != 0:
        purgedparticles, purgednumber = maxdefocus(particles2use, params["parser_maxdefocus"])
        writestar(purgedparticles, metadata, params["parser_output"], relegateflag)
        print("\nRemoved " + str(purgednumber) + " particles out of " + str(len(purgedparticles.index)) + " that had defocus values above " + str(params["parser_maxdefocus"]) + " (or " +               str(round(purgednumber*100/totalparticles,1)) + "%).\n-->Output star file: " + params["parser_output"] + "\n")
        sys.exit()
        
    if relegateflag:
        writestar(particles2use, metadata, params["parser_output"], relegateflag)
        print("\nRemoved the optics table and _rlnOpticsGroup.\n-->Output star file: " + params["parser_output"] + "\n")
        sys.exit()
        
    if params["parser_writecol"] != "":
        colstowrite = params["parser_writecol"].split("/")
        outputs = writecol(particles2use, colstowrite)
        print("\nWrote entries from " + str(colstowrite) + "\n-->Output files: " + str(outputs) + " \n")
        sys.exit()
        
    if params["parser_regroup"] != "":
        numpergroup = params["parser_regroup"]
        regroupedparticles = regroup(particles2use, numpergroup)
        writestar(regroupedparticles, metadata, params["parser_output"], relegateflag)
        print("\nRegrouped: " + str(numpergroup) + " particles per group with similar defocus values\n-->Output star file: " + params["parser_output"] + " \n")
        sys.exit()

if __name__ == "__main__":
    params = setupParserOptions()
    mainloop(params)

