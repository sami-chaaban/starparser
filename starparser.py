import sys
import os.path
import pandas as pd
import optparse
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

def setupParserOptions():
    
    parser = optparse.OptionParser(usage="Usage: %prog --i starfile [options]",
        version="%prog 1.16.")

    parser.add_option("--i",
        action="store", dest="file", default="", metavar='starfile',
        help="Input file name.")

    parser.add_option("--f",
        action="store", dest="parser_file2", default="", metavar='other-starfile',
        help="Name of second file to get information from, if necessary.")
    
    plot_opts = optparse.OptionGroup(
        parser, 'Plotting Options')

    plot_opts.add_option("--histogram",
        action="store", dest="parser_plot", default="", metavar="column-name",
        help="Plot values of a column as a histogram. Optionally, use --c and --q to only plot a subset of particles, otherwise it will plot all. The filename will be that of the column name. Use --t to change the filetype.")

    plot_opts.add_option("--plot_orientations",
        action="store_true", dest="parser_plotangledist", default=False,
        help="Plot the particle orientations based on the _rlnAngleRot and _rlnAngleTilt columns on a Mollweide projection (longitude and lattitude, respectively). Optionally, use --c and --q to only plot a subset of particles, otherwise it will plot all. Use --t to change the filetype.")
    
    plot_opts.add_option("--plot_class_iterations",
        action="store", dest="parser_classdistribution", type="string", default="", metavar="classes",
        help="Plot the number of particles per class for all iterations up to the one provided in the input (skips iterations 0 and 1). Type \"all\" to plot all classes or separate the classes you want with a dash (e.g. 1/2/5). Use --t to change filetype.")
    
    plot_opts.add_option("--plot_class_proportions",
        action="store_true", dest="parser_classproportion", default=False,
        help="Plot the proportion of particles that match different queries in each class. At least two queries (--q, separated by slashes) must be provided along with the column to search in (--c). It will output the proportions and plot the result in Class_proportion.png. Use --t to change filetype.")

    plot_opts.add_option("--plot_coordinates",
        action="store", dest="parser_comparecoords", type="string", default="", metavar="xlimit/ylimit",
        help="Plot the particle coordinates for the input star file for each micrograph in a multi-page pdf (black circles). The argument to pass is the x and y limits of the plot (i.e. the size of the micrographs) in pixels (e.g. 5760/4096). Use --f to overlay the coordinates of a second star file (blue dots); in this case, the micrograph names should match between the two star files. This option is useful to compare coordinates after filtering a dataset. The plots are output to Coordinates.pdf. Optionally, pass a third argument to specify how many micrographs to plot (e.g. *5760/4096/100* to do the first 100 micrographs).")

    parser.add_option_group(plot_opts)
    
    modify_opts = optparse.OptionGroup(
        parser, 'Modification Options')

    modify_opts.add_option("--operate",
        action="store", dest="parser_operate", type="string", default="", metavar='column[operator]value',
        help="Perform operation on all values of a column. The argument to pass is column[operator]value (without the brackets and without any spaces); operators include \"*\", \"/\", \"+\", and \"-\" (e.g. _rlnHelicalTrackLength*0.25).")
    
    modify_opts.add_option("--delete_column",
        action="store", dest="parser_delcolumn", type="string", default="", metavar='column-name(s)',
        help="Delete column and renumber headers. E.g. _rlnMicrographName. To enter multiple columns, separate them with a slash: _rlnMicrographName/_rlnCoordinateX.")
    
    modify_opts.add_option("--delete_particles",
        action="store_true", dest="parser_delparticles", default=False,
        help="Delete particles. Pick a column header (--c) and query (--q) to delete particles that match it.")

    modify_opts.add_option("--delete_duplicates",
        action="store", dest="parser_delduplicates", default="", metavar='column-name',
        help="Delete duplicate particles based on the column provided here (e.g. _rlnImageName).")

    modify_opts.add_option("--delete_mics_fromlist",
        action="store_true", dest="parser_delmics", default=False,
        help="Delete particles that belong to micrographs that have a match in a second file provided by --f.")

    modify_opts.add_option("--insert_column",
        action="store", dest="parser_insertcol", type="string", default="", metavar='column-name',
        help="Insert a new column that has the values found in the file provided by --f. The file should be a single column and should have an equivalent number to the star file.")     

    modify_opts.add_option("--replace_column",
        action="store", dest="parser_replacecol", type="string", default="", metavar='column-name',
        help="Replace all entries of a column with a list of values found in the file provided by --f. The file should be a single column and should have an equivalent number to the star file.")     

    modify_opts.add_option("--copy_column",
        action="store", dest="parser_copycol", type="string", default="", metavar='source-column/target-column',
        help="Replace all entries of a target column with those of a source column in the same star file. If the target column exists, its values will be replaced. If the target does not exist, a new column will be made. The argument to pass is source-column/target-column (e.g. _rlnAngleTiltPrior/_rlnAngleTilt)")     

    modify_opts.add_option("--reset_column",
        action="store", dest="parser_resetcol", type="string", default="", metavar='column-name/new-value',
        help="Change all values of a column to the one provided here. The argument to pass is column-name/new-value (e.g. _rlnOriginX/0).")

    modify_opts.add_option("--swap_columns",
        action="store", dest="parser_swapcolumns", type="string", default="", metavar='column-name(s)',
        help="Swap columns from another star file (specified with --f). E.g. _rlnMicrographName. To enter multiple columns, separate them with a slash: _rlnMicrographName/_rlnCoordinateX.")

    modify_opts.add_option("--fetch_from_nearby",
        action="store", dest="parser_fetchnearby", type="string", default="", metavar='distance/column-name(s)',
        help="Find the nearest particle in a second star file (specified by --f) and if it is within a threshold distance, retrieve its column value to replace the original particle column value. The argument to pass is distance/column-name (e.g. 300/_rlnClassNumber). Particles that couldn't be matched to a neighbor will be skipped (i.e. if the second star file lacks particles in that micrograph). The micrograph paths from _rlnMicrographName do not necessarily need to match, just the filenames need to.")

    modify_opts.add_option("--import_mic_values",
        action="store", dest="parser_importmicvalues", type="string", default="", metavar='column-name',
        help="For every particle, find the equivalent micrograph in a second star file provided by --f and replace its column value with that of the second star file (e.g. _rlnOpticsGroup). This requires that the second star file only has one instance of each micrograph name. To import multiple columns, separate them with a slash.")

    modify_opts.add_option("--regroup",
        action="store", dest="parser_regroup", type="int", default=0, metavar='particles-per-group',
        help="Regroup particles such that those with similar defocus values are in the same group. Any value can be entered. This is useful if there aren't enough particles in each micrograph to make meaningful groups. Note that Subset selection in Relion can also regroup.")

    modify_opts.add_option("--new_optics",
        action="store", dest="parser_newoptics", type="string", default="", metavar='opticsgroup-name',
        help="Provide a new optics group name. Use --c and --q to specify which particles belong to this optics group. The optics values from the last entry of the optics table will be duplicated.")

    modify_opts.add_option("--relegate",
        action="store_true", dest="parser_relegate", default=False,
        help="Remove optics table and optics column and write to a new star file so that it is compatible with Relion 3.0.")

    parser.add_option_group(modify_opts)
    
    info_opts = optparse.OptionGroup(
        parser, 'Data Mining Options')

    info_opts.add_option("--extract_particles",
        action="store_true", dest="parser_extractparticles", default=False,
        help="Write a star file with particles that match a column header (--c) and query (--q).")

    info_opts.add_option("--limit_particles",
        action="store", dest="parser_limitparticles", type="string", default = "", metavar='column/comparator/value',
        help="Extract particles that match a specific operator (\"lt\" for less than, \"gt\" for greater than). The argument to pass is column/comparator/value (e.g. \"_rlnDefocusU/lt/40000\" for defocus values less than 40000).")
    
    info_opts.add_option("--count_particles",
        action="store_true", dest="parser_countme", default=False,
        help="Count particles and print the result. Optionally, use --c and --q to count a subset of particles, otherwise counts all.")
    
    info_opts.add_option("--count_mics",
        action="store_true", dest="parser_uniquemics", default=False,
        help="Count the number of unique micrographs. Optionally, use --c and --q to count from a subset of particles, otherwise counts all.")
    
    info_opts.add_option("--list_column",
        action="store", dest="parser_writecol", type="string", default="", metavar='column-name(s)',
        help="Write all values of a column to a file. For example, passing \"_rlnMicrographName\" will write all values to MicrographName.txt. To output multiple columns, separate the column names with a slash (for example, \"_rlnMicrographName/_rlnCoordinateX\" outputs MicrographName.txt and CoordinateX.txt). This can be used with --c and --q to only consider values that match the query, otherwise it lists all values.")

    info_opts.add_option("--find_shared",
        action="store", dest="parser_findshared", type="string", default="", metavar='column-name',
        help="Find particles that are shared between the input star file and the one provided by --f based on the column provided here. Two new star files will be output, one with the shared particles and one with the unique particles.")

    info_opts.add_option("--extract_if_nearby",
        action="store", dest="parser_findnearby", type="float", default=-1, metavar='distance',
        help="Find the nearest particle in a second star file (specified by --f); particles that have a neighbor in the second star file closer than the distance provided here will be output to particles_close.star and those that don't will be output to particles_far.star. Particles that couldn't be matched to a neighbor will be skipped (i.e. if the second star file lacks particles in that micrograph). It will also output a histogram of nearest distances to Particles_distances.png.")

    info_opts.add_option("--extract_clusters",
        action="store", dest="parser_cluster", type="string", default="", metavar='threshold-distance/minimum-per-cluster',
        help="Extract particles that have a minimum number of neighbors within a given radius. For example, passing \"400/4\" extracts particles with at least 4 neighbors within 400 pixels.")

    info_opts.add_option("--random",
        action="store", dest="parser_randomset", type="int", default=-1, metavar='number',
        help="Get a random set of particles totaling the number provided here. Optionally, use --c and --q to extract a random set of each passed query in the specified column. In this case, the output star files will have the names of the query.")

    info_opts.add_option("--split",
        action="store", dest="parser_split", type="int", default=-1, metavar='number',
        help="Split the input star file into the number of star files passed here, making sure not to separate particles that belong to the same micrograph. The files will have the input file name with the suffix \"_split-#\". Note that they will not necessarily contain exactly the same number of particles")

    info_opts.add_option("--split_classes",
        action="store_true", dest="parser_splitclasses", default=False,
        help="Split the input star file into independent star files for each class. The files will have the names \"Class_#.star\".") 

    info_opts.add_option("--split_optics",
        action="store_true", dest="parser_splitoptics", default=False,
        help="Split the input star file into independent star files for each optics group. The files will have the names of the optics group.")

    info_opts.add_option("--sort_by",
        action="store", dest="parser_sort", type="string", default="", metavar='column-name',
        help="Sort the column in ascending order and output a new file. Add a slash followed by \"n\" if the column contains numeric values (e.g. \"_rlnClassNumber/n\"); otherwise, it will sort the values as text.")   

    parser.add_option_group(info_opts)
    
    query_opts = optparse.OptionGroup(
        parser, 'Query Options')
    
    query_opts.add_option("--c",
        action="store", dest="parser_column", type="string", default="", metavar='column-name(s)',
        help="Column query. E.g. _rlnMicrographName. To enter multiple columns, separate them with a slash: _rlnMicrographName/_rlnCoordinateX.")
    
    query_opts.add_option("--q",
        action="store", dest="parser_query", type="string", default="", metavar='query(ies)',
        help="Particle query term(s) to look for in the values within the specified column. To enter multiple queries, separate them with a slash: 20200101/20200203. Use --e if the query should exactly match the value.")

    query_opts.add_option("--e",
        action="store_true", dest="parser_exact", default=False, metavar="match-exactly",
        help="Pass this if you want an exact match of the values to the query(ies) provided by --q (e.g. if you want just to look for \"1\" and ignore \"15\".)")
    
    parser.add_option_group(query_opts)

    other_opts = optparse.OptionGroup(
        parser, 'Other Options')

    other_opts.add_option("--opticsless",
        action="store_true", dest="parser_optless", default=False,
        help="Pass this if the file lacks an optics group (more specifically: the star file has exactly one table), such as with Relion 3.0 files.")

    parser.add_option_group(other_opts)
    
    output_opts = optparse.OptionGroup(
        parser, 'Output Options')
    
    output_opts.add_option("--o",
        action="store", dest="parser_outname", default = "output.star", metavar='output-name',
        help="Output file name for a star file to be written. Default is output.star")
    
    output_opts.add_option("--t",
        action="store", dest="parser_outtype", default = "png", metavar='plot-filetype',
        help="File type of the plot that will be written. Choose between png, jpg, svg, and pdf. Default is png.")
    
    parser.add_option_group(output_opts)

    ########

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

    opticsstop = 0 #for finding the end of the optics values

    for i in range(4,2000):
        
        if starfilesplit[i] == '#': #When you see a #, it must be the next table starting, so break
            
            opticsstop = i
            
            break
            
    if opticsstop == 0:
        
        print('\n>> Error: Could not find the end of the optics table.\n')
        sys.exit()

    particlesstop = 0 #for finding the end of the particles table headers

    opticstablestop = 0 #for finding the end of the optics table headers
    
    for i in range(5,opticsstop,2):
        
        if starfilesplit[i][0] != "_": #optics table headers start with _, so when it doesn't happen, break
        
            opticstablestop = i
            
            break

    for i in range(opticsstop+5,2000,2):

        if starfilesplit[i][0] != "_":
            
            particlesstop = i
            
            break

    if particlesstop == 0:

        print('\n>> Error: Could not find the end of the particles table.\n')

        sys.exit()
        
    opticstable = starfilesplit[3:opticstablestop]
    
    opticstableheaders = []
    for m in opticstable[::2][1:]: 
        opticstableheaders.append(m)

    version = starfilesplit[0:3]

    optics = starfilesplit[opticstablestop:opticsstop]

    tablename = starfilesplit[opticsstop+3]

    particlestable = starfilesplit[opticsstop+3:particlesstop]
    
    particlestableheaders = []
    for m in particlestable[::2][1:]: 
        particlestableheaders.append(m)

    particles = starfilesplit[particlesstop:]

    return(version,opticstableheaders,optics,particlestableheaders,particles,tablename)

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

    try:

        version, opticsheaders, optics, particlesheaders, particles, tablename = parsestar(starfile)

    except:

        print("\n>> Error: a problem was encountered when trying to parse " + filename + ".\n")
        sys.exit()
    
    alloptics = makepandas(opticsheaders, optics)
    allparticles = makepandas(particlesheaders, particles)
    
    metadata = [version,opticsheaders,alloptics,particlesheaders,tablename]

    return(allparticles, metadata)

def getparticles_dummyoptics(filename):

    file = open(filename,mode='r')
    starfile = file.read()
    file.close()
    tempinsertion = "\n# version 30000\n\ndata_optics\n\nloop_\n_rlnOpticsGroupName #1\n_rlnOpticsGroup #2\n_rlnVoltage #3\n_rlnImagePixelSize #4\nopticsGroup1\t1\t300.000000\t1.000000\n\n\n# version 30000\n\ndata_images\n\n"
    looploc = starfile.find("loop_")
    starfile = tempinsertion + starfile[looploc:]
    version, opticsheaders, optics, particlesheaders, particles, tablename = parsestar(starfile)
    alloptics = makepandas(opticsheaders, optics)
    allparticles = makepandas(particlesheaders, particles)
    metadata = [version,opticsheaders,alloptics,particlesheaders,tablename]

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

        if not params["parser_optless"]:
            print("\n>> Removed the optics table and _rlnOpticsGroup.\n")

    output.write(metadata[4]) #tablename
    output.write('\n\n')
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

    print("-->> Output star file: " + outputname + "\n")

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


    return(iterationfilename[2:]) #skip iteration 0 and 1

def delcolumn(particles, columns, metadata):
    
    nocolparticles = particles.copy()
    
    for c in columns:
        if c not in nocolparticles:
            print("\n>> Error: the column \"" + c + "\" does not exist.\n")
            sys.exit()
        nocolparticles.drop(c, 1, inplace=True)
        metadata[3].remove(c)
    
    return(nocolparticles, metadata)

def countqueryparticles(particles,columns,query,quiet):

    totalparticles = len(particles.index)
    
    totalquery = 0
    
    if len(columns)>1:
        print("\n>> Error: you have specified two different columns.\n")
        sys.exit()

    if columns[0] in ["_rlnClassNumber", "_rlnGroupNumber", "_rlnNrOfSignificantSamples", "_rlnOpticsGroup", "_rlnHelicalTubeID"] and not queryexact and not params["parser_classproportion"]:
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
        
def plotcol(particles, column):
    
    particles[column] = pd.to_numeric(particles[column], downcast="float")

    numparticles = len(particles.index)

    ax = particles[column].plot.hist(bins='fd')
    ax.set_xlabel(column[4:])
    
    fig = ax.get_figure()
    outputfig(fig, column[4:])
    
def plotclassparts(filename, classes):
    
    try:
        classes = list(map(int, classes))
    except:
        print("\n>> Error: could not parse the classes that you passed. Double check that you passed numbers separated by slashes to the --plot_class_iterations option (e.g. 2/6).\n")
        sys.exit()
    
    position = filename.find("_it")
    try:
        iteration = int(filename[position+3:position+6])
    except:
        print("\n>> Error: could not find the iteration number in the filename. The file should be similar to \"run_it025_data.star\".\n")
        sys.exit()
    classdistribution = []
    allparticles, metadata = getparticles(filename)
    numclasses = max(list(map(int, allparticles["_rlnClassNumber"].tolist())))
    iterationfilename = getiterationlist(filename)
    
    print("\n>> Looping through iteration 2 to " + str(iteration) + " on " + str(numclasses) + " classes.")
    if -1 not in classes:
        print("\n>> Only plotting classes " + str(classes) + ".")

    numperclassdf = pd.DataFrame()

    for i in range(len(iterationfilename)):
        iterationfile = iterationfilename[i]
        allparticles, metadata = getparticles(iterationfile)
        numperclass = []
        for c in range(1,numclasses+1):
            numperclass.append(countqueryparticles(allparticles, ["_rlnClassNumber"], [str(c)], True))
        numperclassdf[str(i+2)] = numperclass #set column names to proper iteration number since skipping 0 and 1

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

def plotangledist_old(particles):

    lon=list(map(float, list(particles["_rlnAngleRot"])))
    lat=list(map(float, list(particles["_rlnAngleTilt"])))

    # create some random data for histogram
    lat = [l-90 for l in lat]
    data = [list(a) for a in zip(lon, lat)]
    data = np.array(data) / 180 * np.pi  # shape (n, 2)

    # create bin edges
    bin_number = 50 #this is not always ideal
    lon_edges = np.linspace(-np.pi, np.pi, bin_number + 1)
    lat_edges = np.linspace(-np.pi/2., np.pi/2., bin_number + 1)

    # calculate 2D histogram, the shape of hist is (bin_number, bin_number)
    hist, lon_edges, lat_edges = np.histogram2d(
        *data.T, bins=[lon_edges, lat_edges], density=True
    )

    # generate the plot
    fig = plt.figure(figsize=(3,2))
    ax = fig.add_subplot(111, projection='mollweide')

    cmap='Blues'

    ax.pcolormesh(
        lon_edges[:-1], lat_edges[:-1],
        hist.T,  # transpose from (row, column) to (x, y)
        cmap=cmap,
        shading='gouraud'
    )

    # hide the tick labels
    ax.set_xticks([])
    ax.set_yticks([])

    # add the colorbar
    cbar = plt.colorbar(
            plt.cm.ScalarMappable(
                norm=mpl.colors.Normalize(0, 1), cmap=cmap
            )
        )
    cbar.set_label("Orientation Density")

    outputfig(fig, "Particle_orientations")

def plotangledist(particles):

    import scipy
    from scipy.stats import gaussian_kde

    rot=list(map(float, list(particles["_rlnAngleRot"])))
    tilt=list(map(float, list(particles["_rlnAngleTilt"])))

    ##########################################################################################

    # CODE BELOW ADAPTED FROM SIMILAR FUNCTION BY ISRAEL FERNANDEZ

    ###############

    tilt_m90 = [i -90 for i in tilt]
    rot_rad = np.deg2rad(rot)
    tilt_m90_rad = np.deg2rad(tilt_m90)
    vertical_rad = np.vstack([tilt_m90_rad, rot_rad])

    try:
        m = gaussian_kde(vertical_rad)(vertical_rad)
    except:
        print("\n>> Error: check the _rlnAngleRot and _rlnAngleTilt columns.\n")
        sys.exit()

    # fig = plt.figure(figsize=(3, 3))
    # plt.hist(rot_rad)
    # outputfig(fig,"rot_rad")

    # fig = plt.figure(figsize=(3, 3))
    # plt.hist(tilt_m90_rad)
    # outputfig(fig,"tilt_m90_rad")

    fig = plt.figure(figsize=(3.5, 1.8))
    ax = plt.subplot(111, projection="mollweide")

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ax.scatter(rot_rad, tilt_m90_rad, cmap="Blues", c=m, s=3, alpha=0.1)

    ax.set_xticklabels([])
    ax.set_yticklabels([])

    #x_60_rad = [1.047 for i in range(0,7)]
    #x_m60_rad = [-1.047 for i in range(0,7)]
    #x_120_rad = [2.094 for i in range(0,7)]
    #x_m120_rad = [-2.094 for i in range(0,7)]

    """These two lines draw curved lines at x -120, -60, 60, 120."""
    #ax.plot(x_60_rad, np.arange(-1.5, 2, 0.5), color='k', lw=1.5, linestyle=':')
    #ax.plot(x_m60_rad, np.arange(-1.5, 2, 0.5), color='k', lw=1.5, linestyle=':')
    #ax.plot(x_120_rad, np.arange(-1.5, 2, 0.5), color='k', lw=1.5, linestyle=':')
    #ax.plot(x_m120_rad, np.arange(-1.5, 2, 0.5), color='k', lw=1.5, linestyle=':')
    """These two lines draw vertical and horizontal straight lines as x, y cartesian axes."""
    #ax.vlines(0,-1.6,1.6, colors='k', lw=1.5, linestyles=':')
    #ax.hlines(0,-10,10, colors='k', lw=1.5, linestyles=':')

    #########################################################################################################

    # SHOW COLOR BAR

    cbar = plt.colorbar(
            plt.cm.ScalarMappable(
                norm=mpl.colors.Normalize(0, 1), cmap="Blues"
            ), shrink=0.6, pad = 0.1#cax = fig.add_axes([0.92, 0.33, 0.03, 0.38])
        )
    cbar.set_label("Orientation Density")

    plt.tight_layout(pad=0.2)

    outputfig(fig, "Particle_orientations")

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

def delparticles(particles, columns, query):
    
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

def extractparticles(particles, columns, query):
    
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
    except:
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
    
def checksubset(particles, params):
    
    if params["parser_column"] != "" and params["parser_query"] != "":
        query = params["parser_query"].split("/")
        columns = params["parser_column"].split("/")
        subsetparticles, extractednumber = extractparticles(particles, columns, query)
        
        print("\n>> Created a subset of " + str(extractednumber) + " particles (out of " + str(len(particles.index)) + ", " + str(round(extractednumber*100/len(particles.index),1)) + "%) that match " + str(query) +               " in the columns " + str(columns) + ".")
        
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

def classproportion(particles, columns, query):

    totalqueried = len(query)
    
    if totalqueried < 2:
        print("\n>> Error: enter at least two queries separated by a slash.\n")
        sys.exit()

    subsetparticles, totalsubset = extractparticles(particles, columns, query)

    if len(subsetparticles.index) == 0:
        print("\n>> Error: no classes seem to contain the desired queries in the specified column.\n")
        sys.exit()

    classestocheck = list(set(subsetparticles["_rlnClassNumber"]))
    classestocheck_int = [int(i) for i in classestocheck]
    classestocheck_int.sort()
    classestocheck = [str(i) for i in classestocheck_int]

    percentparts_lst = []

    for c in classestocheck:

        sub_subsetparticles = subsetparticles[subsetparticles["_rlnClassNumber"] == c]
        totalclasssubsubset = len(sub_subsetparticles)
        percentparts = []

        for q in query:
            totalclasspartsinsubset = countqueryparticles(sub_subsetparticles, columns, [q], True)
            percentparts.append(totalclasspartsinsubset*100 / totalclasssubsubset)

        percentparts_lst.append(percentparts)
    
    print("\n>> There are " + str(len(classestocheck)) + " classes that contain the queries. Checking the proportion of " + str(query) + ".")

    for i,c in enumerate(classestocheck):

        print("\nClass " + c)
        print("--------")

        for j,q in enumerate(query):

            print("·" + q + ": " + str(round(percentparts_lst[i][j],1)) + "%")

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

    if len(classestocheck)/3.5 < 6:
        figwidth = 6
    else:
        figwidth = len(classestocheck)/3.5
    fig = plt.figure(figsize=(figwidth,5))

    for q in list(reversed(range(totalqueried))):

        plt.bar(classestocheck, percentparts_reordered[q], 0.32)

    plt.legend(list(reversed(query)), bbox_to_anchor=(1.04,1))
    plt.ylabel('Percent of Particles')
    plt.xlabel('Class Number')
    plt.tight_layout()
    
    outputfig(fig, "Class_proportion")

def outputfig(fig, name):
    
    fig.savefig(name + "." + outtype, dpi=300)
    print("\n-->> Output figure to " + name + "." + outtype + ".\n")
    
def makeopticsgroup(particles,metadata,newgroup):
    
    optics = metadata[2]
    
    newoptics = optics.append(optics.loc[len(optics.index)-1], ignore_index = True)
    
    newoptics.loc[len(newoptics.index)-1]["_rlnOpticsGroupName"] = newgroup
    
    opticsnumber = int(newoptics.loc[len(newoptics.index)-1]["_rlnOpticsGroup"]) + 1
    
    newoptics.loc[len(newoptics.index)-1]["_rlnOpticsGroup"] = opticsnumber
    
    return(newoptics, opticsnumber)
    
def setparticleoptics(particles,column,query,opticsnumber):
    
    particlesnewoptics = particles.copy()

    numchanged = countqueryparticles(particles, column, query, True)
    
    if not queryexact:
        q = "|".join(query)
        particlesnewoptics.loc[particles[column[0]].str.contains(q), "_rlnOpticsGroup"] = opticsnumber
    else:
        for q in query:
            particlesnewoptics.loc[particles[column[0]]==q, "_rlnOpticsGroup"] = opticsnumber
        
    return(particlesnewoptics, numchanged)

def splitparts(particles,numsplits):

    totalparticles = len(particles.index)

    splitnum = int(totalparticles/numsplits)

    start = 0
    end = splitnum

    splitstars = []

    for i in range(numsplits):

        currentmic = particles["_rlnMicrographName"][end]
        
        j = end

        if j != totalparticles:

            while particles["_rlnMicrographName"][j] == particles["_rlnMicrographName"][end]:
                j+=1
                if j == totalparticles:
                    break

        end = j

        splitstars.append(particles.iloc[start:end,:])

        start = j
        end = j+splitnum

        if end > totalparticles-1:
            end = totalparticles-1

    return(splitstars)

def splitbyoptics(particles,metadata):
    print("")
    for n,o in zip(metadata[2]["_rlnOpticsGroup"],metadata[2]["_rlnOpticsGroupName"]):
        subsetoptics, subsetopticslength = extractparticles(particles,["_rlnOpticsGroup"],[n])
        newmetadata = [metadata[0], metadata[1], metadata[2][metadata[2]["_rlnOpticsGroupName"] == o], metadata[3], metadata[4]]
        print(">> Optics group " + str(n) + " has " + str(subsetopticslength) + " particles.")
        writestar(subsetoptics, newmetadata, o+".star", False)

def splitbyclass(particles,metadata,relegateflag):
    classes = list(set(particles["_rlnClassNumber"]))   
    classes = sorted(list(map(int, classes)))
    for c in classes:
        classparticles, classparticleslength = extractparticles(particles,["_rlnClassNumber"],[str(c)])
        print("\n>> Class " + str(c) + " has " + str(classparticleslength) + " particles.")
        writestar(classparticles, metadata, "Class_"+str(c)+".star", relegateflag)
    print("")

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

    print("\n>> Created subsets with particles that are closer or further than " + str(threshdist) + " pixels from the closest particle in the second star file. Out of " + str(len(coreparticles.index)) + ", the subsets have:\n-FAR: " + str(len(farparticles.index)) + " particles\n-CLOSE: " + str(len(closeparticles.index)) + " particles\n-NO-MATCH: " + str(len(noparts)) + " particles\n")

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


def comparecoords(file1parts,file2parts,limits,numtoplot):

    file1parts["_rlnMicrographName"] = file1parts["_rlnMicrographName"].str.split('/').str[-1]

    file1mics = file1parts.groupby(["_rlnMicrographName"])
    file1xloc = file1parts.columns.get_loc("_rlnCoordinateX")+1
    file1yloc = file1parts.columns.get_loc("_rlnCoordinateY")+1
    file1nameloc = file1parts.columns.get_loc("_rlnImageName")+1
    if not file2parts.empty:
        file2parts["_rlnMicrographName"] = file2parts["_rlnMicrographName"].str.split('/').str[-1]
        file2mics = file2parts.groupby(["_rlnMicrographName"])
        file2xloc = file2parts.columns.get_loc("_rlnCoordinateX")+1
        file2yloc = file2parts.columns.get_loc("_rlnCoordinateY")+1

    fig = plt.figure()

    try:
        pdf = PdfPages('Coordinates.pdf')
    except:
        print("\n>> Error: could not save to Compare_coordinates.pdf. Is it still open?\n")
        sys.exit()

    if not file2parts.empty:
        print("\n>> Plotting coordinates from the star file (black circles) and second file (blue dots) for each micrograph.")
    else:
        print("\n>> Plotting coordinates from the star file (black circles) for each micrograph.")

    count=0

    for file1mic in file1mics:

        count+=1

        skipflag = False
        try:
            file2mic = file2mics.get_group(file1mic[0])
        except:
            skipflag = True
            
        mic = file1mic[0] #.split("/")[-1]
        
        fig, ax = plt.subplots(figsize=(5.63,4.09))
        
        for file1part in file1mic[1].itertuples():
            x1 = float(file1part[file1xloc])
            y1 = float(file1part[file1yloc])
            plt.scatter(x1,y1, color='black', facecolors='none', s=150, alpha=0.8, linewidth = 1.8)

        if not skipflag and not file2parts.empty:
            for file2part in file2mic.itertuples():
                x2 = float(file2part[file2xloc])
                y2 = float(file2part[file2yloc])
                plt.scatter(x2,y2, color='blue', s=20, alpha=0.8, linewidth = 1)

        plt.title(mic, fontsize = 8)
        plt.xlim(0,int(limits[0]))
        plt.ylim(0,int(limits[1]))
        plt.xlabel("Pixels")
        plt.ylabel("Pixels") 
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close('all')

        if count == numtoplot:
            break

    pdf.close()

    print("-->> Output figure to Coordinates.pdf\n")
        
################################################################################################################
################################################################################################################
################################################################################################################
################################################################################################################
    
def mainloop(params):
    
    ##############################################################
    
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
    
    global outtype
    outtype = params["parser_outtype"]

    global queryexact
    queryexact = params["parser_exact"]
    if queryexact:
        print("\n>> You have asked starparser to look for exact matches between the queries and values.")
    elif params["parser_splitoptics"] or params["parser_classdistribution"] or params["parser_splitclasses"]:
        queryexact = True
    
    #####################################################################
    
    #Set up jobs that don't require initialization
    
    if params["parser_classdistribution"] != "":
        if params["parser_classdistribution"] == "all":
            plotclassparts(filename, [-1])
        else:
            plotclassparts(filename,params["parser_classdistribution"].split("/"))
        sys.exit()
    
    #########################################################################
    
    #Initialize variables

    if params["parser_optless"]: #add dummy optics table
        allparticles, metadata = getparticles_dummyoptics(filename)
        #print("\n>> Created a dummy optics table to read this star file.")
    else:
        allparticles, metadata = getparticles(filename)

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
        countqueryparticles(allparticles, columns, query, False)
        sys.exit()
    elif params["parser_countme"]:
        print('\n>> There are ' + str(totalparticles) + ' particles in total.\n') 
        sys.exit()
        
    if params["parser_delcolumn"] != "":
        columns = params["parser_delcolumn"].split("/")
        newparticles, metadata = delcolumn(allparticles, columns, metadata)
        print("\n>> Removed the columns " + str(columns))
        writestar(newparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()
        
    if params["parser_delparticles"]:
        if params["parser_query"] == "" or params["parser_column"] == "":
            print("\n>> Error: provide a column (--c) and query (--q) to find specific particles to remove.\n")
            sys.exit()
        newparticles = delparticles(allparticles, columns, query)
        purgednumber = len(allparticles.index) - len(newparticles.index)
        print("\n>> Removed " + str(purgednumber) + " particles (out of " + str(totalparticles) + ", " + str(round(purgednumber*100/totalparticles,1)) + "%) that matched " + str(query) + " in the column " + params["parser_column"] + ".")
        writestar(newparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_delduplicates"] != "":
        column = params["parser_delduplicates"]
        if column not in allparticles:
            print("\n>> Error: the column " + str(column) + " does not exist in your star file.\n")
            sys.exit()
        newparticles = delduplicates(allparticles, column)
        purgednumber = len(allparticles.index) - len(newparticles.index)
        newtotal = len(newparticles.index)
        print("\n>> Removed " + str(purgednumber) + " particles (out of " + str(totalparticles) + ", " + str(round(purgednumber*100/totalparticles,1)) + "%) that were duplicates based on the " + column + " column.")
        print(">> The new total is " + str(newtotal) + " particles.")
        writestar(newparticles, metadata, params["parser_outname"], relegateflag)
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
        newparticles = delmics(allparticles,micstodelete)
        purgednumber = len(allparticles.index) - len(newparticles.index)
        print("\n>> Removed " + str(purgednumber) + " particles (out of " + str(totalparticles) + ", " + str(round(purgednumber*100/totalparticles,1)) + "%) that matched the micrographs in " + file2 + ".")
        writestar(newparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()
        
    if params["parser_swapcolumns"] != "":
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to swap columns from.\n")
            sys.exit()
        file2 = params["parser_file2"]
        if not os.path.isfile(file2):
            print("\n>> Error: \"" + file2 + "\" does not exist.\n")
            sys.exit();
        otherparticles, metadata2 = getparticles(file2)
        columnstoswap = params["parser_swapcolumns"].split("/")
        swappedparticles = swapcolumns(allparticles, otherparticles, columnstoswap)
        print("\n>> Swapped in " + str(columnstoswap) + " from " + file2)
        writestar(swappedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_importmicvalues"] != "":
        if params["parser_file2"] == "":
            print("\n>> Error: provide a second file with --f to import values from.\n")
            sys.exit()
        file2 = params["parser_file2"]
        if not os.path.isfile(file2):
            print("\n>> Error: \"" + file2 + "\" does not exist.\n")
            sys.exit();
        otherparticles, metadata2 = getparticles(file2)
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

        #this is very inefficient
        importedparticles = allparticles.copy()
        for column in columnstoimport:
            importedparticles = importmicvalues(importedparticles, otherparticles, column)

        print("\n>> Imported " + str(columnstoimport) + " from " + file2)
        writestar(importedparticles, metadata, params["parser_outname"], relegateflag)
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
        except:
            print("\n>> Error: Could not interpret \"" + value + "\" as numeric.\n")
            sys.exit()      
        if column not in allparticles:
            print("\n>> Error: Could not find the column " + column + " in the star file.\n")
            sys.exit()  

        operatedparticles = operate(allparticles,column,operator,value)
        writestar(operatedparticles, metadata, params["parser_outname"], relegateflag)
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
        otherparticles, metadata = getparticles(file2)
        unsharedparticles = allparticles[~allparticles[columntocheckunique].isin(otherparticles[columntocheckunique])]
        sharedparticles = allparticles[allparticles[columntocheckunique].isin(otherparticles[columntocheckunique])]
        if params["parser_findshared"] != "":
            print("\nShared: \n-------\n" + str(len(sharedparticles.index)) + " particles are shared between " + filename + " and " + file2 + " in the " + str(columntocheckunique) + " column.\n")
            writestar(sharedparticles, metadata, "shared.star", relegateflag)
            print("Unique: \n-------\n·" + filename + ": " + str(len(unsharedparticles.index)) + " particles (these will be written to unique.star)\n·" + file2 + ": " + str(len(otherparticles.index) - len(sharedparticles.index)) + " particles\n")
            writestar(unsharedparticles, metadata, "unique.star", relegateflag)
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

        nearparticles, nearmetadata = getparticles(params["parser_file2"])
        farparticles, closeparticles, distances = findnearby(allparticles, nearparticles, threshdist)

        fig = plt.figure()
        plt.hist(distances, bins='fd', color = 'k', alpha=0.5)
        plt.axvline(x=threshdist, linestyle='--', color = 'maroon')
        plt.ylabel('Frequency')
        plt.xlabel('Nearest distance')
        outputfig(fig, "Particle_distances")

        writestar(closeparticles, metadata, "particles_close.star", relegateflag)
        writestar(farparticles, metadata, "particles_far.star", relegateflag)

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
        nearparticles, nearmetadata = getparticles(params["parser_file2"])
        for c in columnstoretrieve:
            if c not in nearparticles:
                print("\n>> Error: " + c + " does not exist in the second star file.\n")
                sys.exit()
        print("\n>> Fetching " + str(columnstoretrieve) + " values from particles within " + str(threshdist) + " pixels.\n")
        stolenparticles = fetchnearby(allparticles, nearparticles, threshdist, columnstoretrieve)
        writestar(stolenparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_cluster"] != "":
        retrieveparams = params["parser_cluster"].split("/")
        if len(retrieveparams) != 2:
            print("\n>> Error: provide argument in this format: threshold-distance/minimum-per-cluster (e.g. 400/4).")
            sys.exit()
        threshold = float(retrieveparams[0])
        minimum = int(retrieveparams[1])
        print("\n>> Extracting particles that have at least " + str(minimum) + " neighbors within " + str(threshold) + " pixels.\n")
        clusterparticles = getcluster(allparticles, threshold,minimum)
        writestar(clusterparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()
        
    if params["parser_classproportion"]:
        if params["parser_query"] == "":
            print("\n>> Error: you have not entered a query.\n")
            sys.exit()
        elif params["parser_column"] == "":
            print("\n>> Error: you have not entered a column.\n")
            sys.exit()
        classproportion(allparticles, columns, query)
        sys.exit()
        
    if params["parser_newoptics"] !="":
        newgroup = params["parser_newoptics"]
        newoptics, opticsnumber = makeopticsgroup(allparticles,metadata,newgroup)
        metadata[2] = newoptics
        if params["parser_column"] == "" or params["parser_query"] == "":
            print("\n>> Error: you did not enter either an optics group name, column name, or query(ies).\n")
            sys.exit()
        particlesnewoptics, newopticsnumber = setparticleoptics(allparticles,columns,query,str(opticsnumber))
        print("\n>> Created optics group called " + newgroup + " (optics group " + str(opticsnumber)+") for the " + str(newopticsnumber) + " particles that match " + str(query) + " in the column " + str(columns))
        writestar(particlesnewoptics,metadata,params["parser_outname"],False)
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
        limitedparticles = limitparticles(allparticles, columntocheck, limit, operator)
        if operator == "lt":
            print("\n>> Extracted " + str(len(limitedparticles.index)) + " particles (out of " + str(totalparticles) + ", " + str(round(len(limitedparticles.index)*100/totalparticles,1)) + "%) that have " + str(columntocheck) + " values less than " + str(limit))
        elif operator == "gt":
            print("\n>> Extracted " + str(len(limitedparticles.index)) + " particles (out of " + str(totalparticles) + ", " + str(round(len(limitedparticles.index)*100/totalparticles,1)) + "%) that have " + str(columntocheck) + " values greater than " + str(limit))
        writestar(limitedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_randomset"] != -1:
        numrandom = params["parser_randomset"]
        if numrandom == 0:
            print("\n>> Error: you cannot pass 0 particles.\n")
        if numrandom > len(allparticles.index):
            print("\n>> Error: the number of particles you want to randomly extract cannot be greater than the total number of particles (" + str(len(allparticles.index)) + ").\n")
        if params["parser_column"] == "" and params["parser_query"] == "":
            print("\n>> Creating a random set of " + str(numrandom) + " particles.")
            writestar(allparticles.sample(n = numrandom), metadata, params["parser_outname"], relegateflag)
        elif params["parser_column"] == "" or params["parser_query"] == "":
            print("\n>> Error: check that you have passed the column and query arguments correctly.\n")
        else:
            for q in query:
                print("\n>> Creating a random set of " + str(numrandom) + " particles that match " + q)
                randomsettowrite, totalnum = extractparticles(allparticles,columns,[q])
                if totalnum < numrandom and totalnum != 0:
                    print("\n>> Warning: the query " + q + " has less particles than the requested number!\n")
                elif totalnum == 0:
                    print("\n>> Error: the query " + q + " has 0 particles in the specified column.\n")
                    sys.exit()
                writestar(randomsettowrite.sample(n = numrandom), metadata, q+"_"+str(numrandom)+".star", relegateflag)
        sys.exit()

    if params["parser_split"] != -1:
        numsplits = params["parser_split"]
        if numsplits == 1:
            print("\n>> Error: you cannot split into 1 part.\n")
            sys.exit()
        if numsplits > len(allparticles.index):
            print("\n>> Error: you cannot split into more parts than there are particles.\n")
            sys.exit()
        splitstars = splitparts(allparticles,numsplits)
        print("\n")
        fill = len(str(len(splitstars)))
        for i,s in enumerate(splitstars):
            print(">> There are " + str(len(s.index)) + " particles in file " + str(i+1))
            writestar(s, metadata, filename[:-5]+"_split-"+str(i+1).zfill(fill)+".star", relegateflag)
        sys.exit()

    if params["parser_splitoptics"]:
        splitbyoptics(allparticles,metadata)
        sys.exit()

    if params["parser_splitclasses"]:
        if "_rlnClassNumber" not in allparticles:
            print("\n>> Error: _rlnClassNumber does not exist in the star file.")
        splitbyclass(allparticles,metadata,relegateflag)
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
        writestar(allparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_comparecoords"] != "":
        if params["parser_file2"] == "":
            file2particles = pd.DataFrame({'A' : []})
        else:
            file2particles, metadata = getparticles(params["parser_file2"])
        retrieveparams = params["parser_comparecoords"].split("/")
        if len(retrieveparams) < 2 or len(retrieveparams) > 3:
            print("\n>> Error: provide argument in this format: xlimit/ylimit (e.g. 5760/4092).")
            sys.exit()
        elif len(retrieveparams) == 2:
            limits = retrieveparams
            numtoplot = len(allparticles.index)
        elif len(retrieveparams) == 3:
            limits = retrieveparams[0:2]
            numtoplot = int(retrieveparams[2])
        comparecoords(allparticles, file2particles, limits, numtoplot)
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
        replacedstar = replacecolumn(allparticles,replacecol,newcol)
        writestar(replacedstar, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_copycol"] != "":

        inputparams = params["parser_copycol"].split("/")
        if len(inputparams) != 2:
            print("\n>> Error: you should provide columns in the form of source-column/target-column.\n")
            sys.exit()
        sourcecol, targetcol = inputparams
        if sourcecol not in allparticles:
            print("\n>> Error: " + sourcecol + " does not exist in the star file.\n")
            sys.exit()
        copiedstar = copycolumn(allparticles,sourcecol,targetcol,metadata)
        writestar(copiedstar, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    if params["parser_resetcol"] != "":

        inputparams = params["parser_resetcol"].split("/")
        if len(inputparams) != 2:
            print("\n>> Error: you should provide columns in the form of column-name/value.\n")
            sys.exit()
        columntoreset, value = inputparams
        if columntoreset not in allparticles:
            print("\n>> Error: " + columntoreset + " does not exist in the star file.\n")
            sys.exit()
        resetstar = resetcolumn(allparticles,columntoreset,value)
        writestar(resetstar, metadata, params["parser_outname"], relegateflag)
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
                print("\n>> Warning: it looks like this column is numeric but you haven't specified so (use \"column/n\"; see documentation). Make sure that this is the behavior you intended.\n")
                print("----------------------------------------------------------------------")
            except:
                pass
            print("\n>> Sorted particles by the column " + sortcol + " assuming the column contains text.")
            writestar(allparticles.sort_values(by=sortcol), metadata, params["parser_outname"], relegateflag)
        elif inputparams[1] == "s":
            try:
                pd.to_numeric(allparticles[sortcol].iloc[0], downcast="float")
                print("\n----------------------------------------------------------------------")        
                print("\n>> Warning: it looks like this column is numeric but you haven't specified so (use \"column/n\"; see documentation). Make sure that this is the behavior you intended.\n")
                print("----------------------------------------------------------------------")
            except:
                pass
            print("\n>> Sorted particles by the column " + sortcol + " assuming the column contains text.")
            writestar(allparticles.sort_values(by=sortcol), metadata, params["parser_outname"], relegateflag)
        elif inputparams[1] == "n":
            try:
                pd.to_numeric(allparticles[sortcol].iloc[0], downcast="float")
            except:
                print("\n>> Error: it looks like this column is NOT numeric but you specified that it is.\n")
                sys.exit()
            allparticles[sortcol] = allparticles[sortcol].apply(pd.to_numeric)
            print("\n>> Sorted particles by the column " + sortcol + " assuming the column contains numeric values.")
            writestar(allparticles.sort_values(by=sortcol), metadata, params["parser_outname"], relegateflag)
        else:
            print("\n>> Error: use \"n\" after the slash to specify that it is numeric.\n")
        sys.exit()

    #######################################################################
    
    #setup SUBSET for remaining functions if necessary
    
    if relegateflag:
        if "_rlnOpticsGroup" in allparticles.columns:
                newparticles, metadata = delcolumn(allparticles, ["_rlnOpticsGroup"], metadata)
                particles2use = checksubset(newparticles, params)
        else:
            particles2use = checksubset(allparticles, params)
    else:      
        particles2use = checksubset(allparticles, params)
    
    if params["parser_uniquemics"]:
        totalmics = len(particles2use["_rlnMicrographName"].unique())
        print("\n>> There are " + str(totalmics) + " unique micrographs in this dataset.\n")
        sys.exit()

    if params["parser_extractparticles"]:
        writestar(particles2use, metadata, params["parser_outname"], relegateflag)
        sys.exit()
        
    if params["parser_plot"] != "":
        columntoplot = params["parser_plot"]
        if columntoplot not in particles2use:
            print("\n>> Error: the column \"" + columntoplot + "\" does not exist.\n")
            sys.exit()
        try:
            plotcol(particles2use, columntoplot)
        except:
            print("\n>> Error: could not plot the column \"" + columntoplot + "\", maybe it's not numeric.\n")
            sys.exit()
        sys.exit()

    if params["parser_plotangledist"]:
        if "_rlnAngleRot" not in particles2use or "_rlnAngleTilt" not in particles2use:
            print("\n>> Error: the column _rlnAngleRot or _rlnAngleTilt does not exist.\n")
            sys.exit()
        print("\n>> Plotting the particle orientations based on the _rlnAngleRot and _rlnAngleTilt on a Mollweide projection.")
        plotangledist(particles2use)
        sys.exit()
        
    if params["parser_writecol"] != "": 
        colstowrite = params["parser_writecol"].split("/")
        for col in colstowrite:
            if col not in particles2use:
                print("\n>> Error: the column \"" + str(col) + "\" does not exist in your star file.\n")
                sys.exit()
        outputs = writecol(particles2use, colstowrite)
        print("\n>> Wrote entries from " + str(colstowrite) + "\n-->> Output files: " + str(outputs) + " \n")
        sys.exit()
        
    if params["parser_regroup"] != 0:
        numpergroup = params["parser_regroup"]
        regroupedparticles, numgroups = regroup(particles2use, numpergroup)
        print("\n>> Regrouped: " + str(numpergroup) + " particles per group with similar defocus values (" + str(numgroups) + " groups in total).")
        writestar(regroupedparticles, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    #This has to be at the end so it only runs if it is the only passed argument.
    if relegateflag and not params["parser_optless"]:
        writestar(particles2use, metadata, params["parser_outname"], relegateflag)
        sys.exit()

    print("\n>> Error: either the options weren't passed correctly or none were passed at all. See the help page (-h).\n")

if __name__ == "__main__":
    params = setupParserOptions()
    mainloop(params)

