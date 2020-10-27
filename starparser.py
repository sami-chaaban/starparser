import sys
import pandas as pd
import optparse
import matplotlib.pyplot as plt

def setupParserOptions():
    
    parser = optparse.OptionParser(usage="Usage: %prog --i starfile [options]",
        version="%prog 1.3.")

    parser.add_option("--i",
        action="store", dest="file", metavar='starfile-name',
        help="Input file name.")
    
    plot_opts = optparse.OptionGroup(
        parser, 'Plotting Options')

    plot_opts.add_option("--plot_defocus",
        action="store_true", dest="parser_plotdefocus", default=False,
        help="Plot defocus to Defocus_histogram.png. Can be used with -c and -q for a subset count, otherwise plots all. Use --t to change filetype.")
    
    plot_opts.add_option("--plot_classparts",
        action="store", dest="parser_classdistribution", type="string", default="", metavar="classes",
        help="Plot the number of particles per class for all iterations up to the one provided in the input. Type \"all\" to plot all classes or separate the classes you want with a dash (e.g. 1/2/5). Use --t to change filetype.")
    
    plot_opts.add_option("--class_proportion",
        action="store_true", dest="parser_classproportion", default=False,
        help="Plot the proportion of particles that match different queries in each class. At least two queries (-q, separated by slashes) must be provided along with the column to search in (-c). It will output the proportions and plot the result in Class_proportion.png. Use --t to change filetype.")

    parser.add_option_group(plot_opts)
    
    modify_opts = optparse.OptionGroup(
        parser, 'Modification Options')
    
    modify_opts.add_option("--extract_particles",
        action="store_true", dest="parser_extractparticles", default=False,
        help="Write a star file with particles that match a column header (-c) and query (-q).")
    
    modify_opts.add_option("--delete_column",
        action="store", dest="parser_delcolumn", type="string", default="", metavar='column-name',
        help="Delete column and renumber headers. E.g. _rlnMicrographName. To enter multiple columns, separate them with a slash: _rlnMicrographName/_rlnCoordinateX.")
    
    modify_opts.add_option("--delete_particles",
        action="store_true", dest="parser_delparticles", default=False,
        help="Delete particles. Pick a column header (-c) and query (-q) to delete particles that match it.")
    
    modify_opts.add_option("--limit_particles",
        action="store", dest="parser_limitparticles", type="string", default = "", metavar='limit',
        help="Extract particles that match a specific operator (\"lt\" for less than, \"gt\" for greater than). The argument to pass is column/operator/value (e.g. \"_rlnDefocusU/lt/40000\" for defocus values less than 40000).")
    
    modify_opts.add_option("--swap_columns",
        action="store", dest="parser_swapcolumns", type="string", default="", metavar='column-name(s)',
        help="Swap columns from another star file (specified with --f). E.g. _rlnMicrographName. To enter multiple columns, separate them with a slash: _rlnMicrographName/_rlnCoordinateX.")
    
    modify_opts.add_option("--relegate",
        action="store_true", dest="parser_relegate", default=False,
        help="Remove optics table and optics column. This may not be sufficient to be fully compatible with Relion 3.0. Use --delete_column to remove other bad columns before this, if necessary.")

    modify_opts.add_option("--regroup",
        action="store", dest="parser_regroup", type="int", default=50, metavar='particles-per-group',
        help="Regroup particles such that those with similar defocus values are in the same group. Any value can be entered. This is useful if there aren't enough particles in each micrograph to make meaningful groups. Note that Subset selection in Relion can also regroup.")

    parser.add_option_group(modify_opts)
    
    info_opts = optparse.OptionGroup(
        parser, 'Data Mining Options')
    
    info_opts.add_option("--count_particles",
        action="store_true", dest="parser_countme", default=False,
        help="Count particles and print the result. Can be used with -c and -q for a subset count, otherwise counts all.")
    
    info_opts.add_option("--count_mics",
        action="store_true", dest="parser_uniquemics", default=False,
        help="Count the number of unique micrographs. Can be used with -c and -q for a subset count, otherwise counts all.")
    
    info_opts.add_option("--list_column",
        action="store", dest="parser_writecol", type="string", default="", metavar='column-name(s)',
        help="Write all values of a column to a file (filename is the header). E.g. _rlnMicrographName. To enter multiple columns, separate them with a slash: _rlnMicrographName/_rlnCoordinateX. Can be used with -c and -q for a subset count, otherwise lists all items.")
    
    info_opts.add_option("--compare_particles",
        action="store", dest="parser_compareparts", type="string", default="", metavar='other-starfile-name',
        help="Count the number of particles that are shared between the input star file and the one provided here. Also counts the number that are unique to each star file.")

    info_opts.add_option("--new_optics",
        action="store", dest="parser_newoptics", type="string", default="", metavar='opticsgroup-name',
        help="Provide a new optics group name. Use -c and -q to specify which particles belong to this optics group. The optics values from the last entry of the optics table will be duplicated; change the values to the correct ones in the output star file.")
    
    parser.add_option_group(info_opts)
    
    query_opts = optparse.OptionGroup(
        parser, 'Query Options')
    
    query_opts.add_option("-c",
        action="store", dest="parser_column", type="string", default="", metavar='column-name(s)',
        help="Column query. E.g. _rlnMicrographName. To enter multiple columns, separate them with a slash: _rlnMicrographName/_rlnCoordinateX.")
    
    query_opts.add_option("-q",
        action="store", dest="parser_query", type="string", default="", metavar='query(ies)',
        help="Particle query. To enter multiple queries, separate them with a slash: 20200101/20200203.")
    
    parser.add_option_group(query_opts)
    
    output_opts = optparse.OptionGroup(
        parser, 'Output Options')
    
    output_opts.add_option("--o",
        action="store", dest="parser_outname", default = "output.star", metavar='output-name',
        help="Output file name for a star file to be written. Default is output.star")
    
    output_opts.add_option("--t",
        action="store", dest="parser_outtype", default = "png", metavar='plot-filetype',
        help="File type of the plot that will be written. Choose between png, jpg, and pdf. Default is png.")
    
    parser.add_option_group(output_opts)

    extra_opts = optparse.OptionGroup(
        parser, 'Miscellaneous Options')
    
    extra_opts.add_option("--f",
        action="store", dest="parser_file2", default="", metavar='other-starfile-name',
        help="Name of second file to extract columns from. Used with --swap_columns.")
    
    parser.add_option_group(extra_opts)

    options,args = parser.parse_args()

    if len(sys.argv) < 4:
            parser.print_help()
            sys.exit()

    params={}

    for i in options.__dict__.items():
        params[i[0]] = i[1]
        
    return(params)

############################################################

def parsestar(starfile):

    starfilesplit = starfile.split()

    version = starfilesplit[0:3]

    opticsstop = 0

    for i in range(4,100):
        
        if starfilesplit[i] == '#':
            
            opticsstop = i
            
            break
            
    if opticsstop == 0:
        
        print('Error: Could not find end of optics table. Exiting.')
        
        sys.exit()

    particlesstop = 0

    opticstablestop = 0
    
    for i in range(5,opticsstop,2):
        
        if starfilesplit[i][0] != "_":
        
            opticstablestop = i
            
            break
            
    for i in range(opticsstop+3,200):

        if starfilesplit[i].replace('.','',1).replace('-','',1).isnumeric() or ".mrc" in starfilesplit[i]:
            
            particlesstop = i
            
            break

    if particlesstop == 0:

        print('Error: Could not find end of particles table. Exiting.')

        sys.exit()
        
    opticstable = starfilesplit[3:opticstablestop]
    
    opticstableheaders = []
    for m in opticstable[::2][1:]: 
        opticstableheaders.append(m)

    optics = starfilesplit[opticstablestop:opticsstop]

    particlestable = starfilesplit[opticsstop+3:particlesstop]
    
    particlestableheaders = []
    for m in particlestable[::2][1:]: 
        particlestableheaders.append(m)

    particles = starfilesplit[particlesstop:]

    return(version,opticstableheaders,optics,particlestableheaders,particles)

#######################################################################################################

def makepandas(headers,items):
    
    totalcolumns = len(headers)

    items_lst = [items[x:x+totalcolumns] for x in range(0, len(items), totalcolumns)]

    itemspd = pd.DataFrame(items_lst, columns = headers)
    
    return(itemspd)

def getparticles(filename):
    
    file = open(filename,mode='r')
    starfile = file.read()
    file.close()

    version, opticsheaders, optics, particlesheaders, particles = parsestar(starfile)
    
    alloptics = makepandas(opticsheaders, optics)
    allparticles = makepandas(particlesheaders, particles)
    
    metadata = [version,opticsheaders,alloptics,particlesheaders]

    return(allparticles, metadata)

def writestar(particles, metadata, outputname, relegate):
    
    output = open(outputname,"w")
    
    output.write('\n')

    version = metadata[0]

    for t in version:
        output.write(t)
        output.write(' ')
    output.write('\n\n')
    
    if not relegate:
        
        optics = metadata[2]

        output.write('data_optics\n\n')
        output.write('loop_')
        
        opticsheaders = metadata[1]
        count=1
        for p in opticsheaders:
            output.write('\n')
            output.write(p)
            output.write(" #"+str(count))
            count += 1
        output.write('\n')
        optics.to_csv(output, header=None, index=None, sep='\t', mode='a')

        output.write('\n\n')
        for t in version:
            output.write(t)
            output.write(' ')
            
        output.write('\n\n')

    else:
        print("\nRemoved the optics table and _rlnOpticsGroup.")

    output.write('data_particles\n\n')
    output.write('loop_')

    headers = metadata[3]
    count=1
    for p in headers:
        output.write('\n')
        output.write(p)
        output.write(" #"+str(count))
        count += 1

    output.write('\n')
    particles.to_csv(output, header=None, index=None, sep='\t', mode='a')

    output.close()

    print("\n-->Output star file: " + outputname + "\n")

def getiterationlist(filename):
    
    position = filename.find("_it")
    iteration = int(filename[position+3:position+6])

    if filename.find("_ct") != -1:

        totalct = filename.count("_ct")
        continueit = []
        for i in range(totalct):
            if i == 0:
                temppos = filename.find("_ct")
                tempendpos = filename[temppos+3:].find("_") + temppos
                continueit.append(filename[temppos+3:tempendpos+3])
            else:
                temppos = filename[tempendpos:].find("_") + tempendpos
                tempendpos = filename[temppos+3:].find("_") + temppos
                continueit.append(filename[temppos+3:tempendpos+3])

        iterationfilename = []
        for ci in range(iteration+1):
            basename = filename[:(filename.find("run_"))] + "run"
            if ci > int(continueit[0])-1:           
                for ccii in continueit:
                    if int(ccii) > ci:
                        continue
                    else:
                        basename = basename + "_ct" + ccii

            iterationfilename.append(basename + "_it" + str(ci).zfill(3) + "_data.star")

    else:

        iterationfilename = []
        for i in reversed(range(0,iteration+1)):
            iterationstring = str(i).zfill(3)
            iterationfilename.append(filename[:position+3] + iterationstring + filename[position+6:])
            
        iterationfilename = iterationfilename[::-1]


    return(iterationfilename)

def delcolumn(particles, columns, metadata):
    
    nocolparticles = particles.copy()
    
    for c in columns:
        if c not in nocolparticles:
            print("\nError: the column \"" + c + "\" does not exist.\n")
            sys.exit()
        nocolparticles.drop(c, 1, inplace=True)
        metadata[3].remove(c)
    
    return(nocolparticles, metadata)

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
    ax.set_xlabel("_rlnDefocusU")
    
    fig = ax.get_figure()
    outputfig(fig, "Defocus_histogram")
    
def plotclassparts(filename, classes):
    
    classes = list(map(int, classes))
    
    position = filename.find("_it")
    iteration = int(filename[position+3:position+6])
    classdistribution = []
    allparticles, metadata = getparticles(filename)
    numclasses = max(list(map(int, allparticles["_rlnClassNumber"].tolist())))
    iterationfilename = getiterationlist(filename)
    
    print("\nLooping through iteration 0 to " + str(iteration) + " on " + str(numclasses) + " classes.")
    if -1 not in classes:
        print("--Only plotting classes " + str(classes) + ".")

    numperclassdf = pd.DataFrame()

    for i in range(len(iterationfilename)):
        iterationfile = iterationfilename[i]
        allparticles, metadata = getparticles(iterationfile)
        numperclass = []
        for c in range(1,numclasses+1):
            numperclass.append(countqueryparticles(allparticles, ["_rlnClassNumber"], [str(c)], True))
        numperclassdf[str(i)] = numperclass

    numperclassdf.index +=1

    for c in range(numclasses):
        test = c+1
        if -1 in classes:
            ax = numperclassdf.iloc[c].plot(kind='line', legend = True, linewidth = 2, alpha = 0.7)
        elif test in classes:
            ax = numperclassdf.iloc[c].plot(kind='line', legend = True, linewidth = 2, alpha = 0.7)
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Particle number")
    fig = ax.get_figure()
    outputfig(fig, "Class_distribution")

def limitparticles(particles, column, limit, operator):
    
    tempcolumnname = column + "_float"
    particles[tempcolumnname] = particles[column]
    particles[tempcolumnname] = pd.to_numeric(particles[tempcolumnname], downcast="float")
    limitedparticles = particles.copy()

    if operator == "lt":
        limitedparticles = limitedparticles[limitedparticles[tempcolumnname]<limit]
    elif operator == "gt":
        limitedparticles = limitedparticles[limitedparticles[tempcolumnname]>limit]
    
    particles.drop(tempcolumnname,1, inplace=True)
    limitedparticles.drop(tempcolumnname,1, inplace=True)
    
    return(limitedparticles)

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

    if len(original_particles.index) != len(swapfrom_particles.index):
        print("\nError: the star files don't have the same number of particles: " + str(len(original_particles.index)) + " vs " + str(len(swapfrom_particles.index)) + ".\n")
        sys.exit()
    
    swappedparticles = original_particles.copy()
    
    for c in columns:
        if c not in original_particles:
            print("\nError: the column \"" + c + "\" does not exist.\n")
            sys.exit()
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

def classproportion(particles, columns, query):

    totalqueried = len(query)
    
    if totalqueried < 2:
        print("\nError: please enter at least two queries separated by a slash.\n")
        sys.exit()

    subsetparticles, totalsubset = extractparticles(particles, columns, query)

    classestocheck = list(set(subsetparticles["_rlnClassNumber"]))
    classestocheck_int = [int(i) for i in classestocheck]
    classestocheck_int.sort()
    classestocheck = [str(i) for i in classestocheck_int]

    percentparts_lst = []

    for c in classestocheck:

        sub_subsetparticles, totalclasssubsubset = extractparticles(subsetparticles,["_rlnClassNumber"], [c])

        percentparts = []

        for q in query:

            totalclasspartsinsubset = countqueryparticles(sub_subsetparticles, columns, [q], True)

            percentparts.append(totalclasspartsinsubset*100 / totalclasssubsubset)

        percentparts_lst.append(percentparts)

    #####################################
    
    print("\nThere are " + str(len(classestocheck)) + " classe(s). Checking the proportion of " + str(query) + "\n")

    for i,c in enumerate(classestocheck):

        print("\nClass " + c)

        for j,q in enumerate(query):

            print("-" + q + ": " + str(round(percentparts_lst[i][j],1)) + "%")

    print("\n")

    #####################################

    def accumu(lis):
        total = 0
        for x in lis:
            total += x
            yield total

    percentparts_cumulative = []

    for c in range(len(classestocheck)):

        percentparts_cumulative.append(list(accumu(percentparts_lst[c])))

    percentparts_reordered = []

    for q in range(totalqueried):

        percentparts_reordered.append([item[q] for item in percentparts_cumulative])

    fig = plt.figure()

    for q in list(reversed(range(totalqueried))):

        plt.bar(classestocheck, percentparts_reordered[q], 0.32)

    plt.legend(list(reversed(query)))
    plt.ylabel('Percent of particles')
    plt.xlabel('Class Number')
    
    outputfig(fig, "Class_proportion")

def outputfig(fig, name):
    
    fig.savefig(name + "." + outtype)
    print("\n-->Output to " + name + "." + outtype + ".\n")
    
def makeopticsgroup(particles,metadata,newgroup):
    
    optics = metadata[2]
    
    newoptics = optics.append(optics.loc[len(optics.index)-1], ignore_index = True)
    
    newoptics.loc[len(newoptics.index)-1]["_rlnOpticsGroupName"] = newgroup
    
    opticsnumber = int(newoptics.loc[len(newoptics.index)-1]["_rlnOpticsGroup"]) + 1
    
    newoptics.loc[len(newoptics.index)-1]["_rlnOpticsGroup"] = opticsnumber
    
    return(newoptics, opticsnumber)
    
def setparticleoptics(particles,column,query,opticsnumber):
    
    particlesnewoptics = particles.copy()
    
    for q in query:
        particlesnewoptics.loc[particles[column[0]].str.contains(q), "_rlnOpticsGroup"] = opticsnumber
        
    return(particlesnewoptics)
        
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
    
    global outtype
    outtype = params["parser_outtype"]
    
    #####################################################################
    
    #Set up jobs that don't require initialization
    
    if params["parser_classdistribution"] != "":
        if params["parser_classdistribution"] == "all":
            plotclassparts(filename, [-1])
        else:
            plotclassparts(filename,params["parser_classdistribution"].split("/"))
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
        print("\nRemoved the columns " + str(columns))
        writestar(newparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()
        
    if params["parser_delparticles"]:
        newparticles = delparticles(allparticles, columns, query)
        purgednumber = len(allparticles.index) - len(newparticles.index)
        print("\nRemoved " + str(purgednumber) + " particles (out of " + str(totalparticles) + ", " + str(round(purgednumber*100/totalparticles,1)) + "%) that matched " + str(query) + " in the column " + params["parser_column"] + ".")
        writestar(newparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()
        
    if params["parser_swapcolumns"] != "":
        if params["parser_file2"] == "":
            print("Error: provide a second file to swap columns from with -f.")
            sys.exit()
        otherparticles, metadata = getparticles(params["parser_file2"])
        columstoswap = params["parser_swapcolumns"].split("/")
        swappedparticles = swapcolumns(allparticles, otherparticles, columstoswap)
        print("\nSwapped in " + str(columstoswap) + " from " + params["parser_file2"])
        writestar(swappedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()
        
    if params["parser_compareparts"] != "":
        otherparticles, metadata = getparticles(params["parser_compareparts"])
        sharedparticles = len(set(allparticles["_rlnImageName"]) & set(otherparticles["_rlnImageName"]))
        unsharedfile1 = len(allparticles["_rlnImageName"]) - sharedparticles
        unsharedfile2 = len(otherparticles["_rlnImageName"]) - sharedparticles
        print("\n" + filename + " and " + params["parser_compareparts"] + " share " + str(sharedparticles) + " particles.")
        print(filename + " has " + str(unsharedfile1) + " unique particles and " + params["parser_compareparts"] + " has " + str(unsharedfile2) + " unique particles.\n")
        sys.exit()
        
    if params["parser_classproportion"]:
        if params["parser_query"] == "":
            print("\nError: you have not entered a query.\n")
            sys.exit()
        elif params["parser_column"] == "":
            print("\nError: you have not entered a column.\n")
            sys.exit()
        classproportion(allparticles, columns, query)
        sys.exit()
        
    if params["parser_newoptics"] !="":
        newgroup = params["parser_newoptics"]
        newoptics, opticsnumber = makeopticsgroup(allparticles,metadata,newgroup)
        metadata[2] = newoptics
        particlesnewoptics = setparticleoptics(allparticles,columns,query,str(opticsnumber))
        print("\nCreated optics group called " + newgroup + " (optics group " + str(opticsnumber)+") for particles that match " + str(query) + " in the column " + str(columns))
        writestar(particlesnewoptics,metadata,params["parser_outname"],False)
        sys.exit()

    if params["parser_limitparticles"] != "":
        parsedinput = params["parser_limitparticles"].split("/")
        if len(parsedinput) > 3:
            print("\nError: provide argument in this format: column/operator/value (e.g. _rlnDefocusU/lt/40000).")
            sys.exit()
        columntocheck = parsedinput[0]
        operator = parsedinput[1]
        limit = float(parsedinput[2])
        limitedparticles = limitparticles(allparticles, columntocheck, limit, operator)
        print("\nExtracted " + str(len(limitedparticles.index)) + " particles (out of " + str(totalparticles) + ", " + str(round(len(limitedparticles.index)*100/totalparticles,1)) + "%) that had " + str(columntocheck) + " values " + operator + " " + str(limit))
        writestar(limitedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()
        
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
        writestar(particles2use, metadata, params["parser_outname"], relegateflag)
        sys.exit()
        
    if params["parser_plotdefocus"]:
        plotdefocus(particles2use)
        sys.exit()
        
    if relegateflag:
        writestar(particles2use, metadata, params["parser_outname"], relegateflag)
        sys.exit()
        
    if params["parser_writecol"] != "":
        colstowrite = params["parser_writecol"].split("/")
        outputs = writecol(particles2use, colstowrite)
        print("\nWrote entries from " + str(colstowrite) + "\n-->Output files: " + str(outputs) + " \n")
        sys.exit()
        
    if params["parser_regroup"] != "":
        numpergroup = params["parser_regroup"]
        regroupedparticles = regroup(particles2use, numpergroup)
        print("\nRegrouped: " + str(numpergroup) + " particles per group with similar defocus values.")
        writestar(regroupedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

if __name__ == "__main__":
    params = setupParserOptions()
    mainloop(params)

