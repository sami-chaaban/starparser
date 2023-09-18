import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import sys
import numpy as np
import os
import scipy
import warnings

from matplotlib.backends.backend_pdf import PdfPages

from scipy.stats import gaussian_kde
from itertools import accumulate

from starparser import fileparser
from starparser import particleplay

"""
--histogram
"""
def plotcol(particles, column, outtype):

    #Check if there are particles to plot. Sometimes, a column/query does not match any particles.
    if len(particles.index) == 0:
        print("\n>> Error: no particles to plot.\n")
        sys.exit()
    
    #Turn all values in the column into float, since by default they are strings
    particles[column] = pd.to_numeric(particles[column], downcast="float")

    #Use matplotlib to plot the histogram. 'fd' stands for Freedman-Diaconis
    ax = particles[column].plot.hist(bins='fd')

    #Label the x-axis with the column name.
    #The 4 is to avoid "_rln" and just have the column name
    ax.set_xlabel(column[4:])
    
    #Get the Figure instance to pass to outputfig() for writing to disk
    fig = ax.get_figure()

    #outputfig takes the Figure instance, the file name (the column name in this case), and file type (passed by the user)
    outputfig(fig, column[4:], outtype)

"""
--plot_class_iterations
"""
def plotclassparts(filename, classes, queryexact, outtype):
    
    #Try turning the list of classes that were passed (which are strings) into integers
    try:
        #map() allows you to iterate a function over a list without a for loop
        #In this case, int() is iterated through the classes list
        #then turned into a list again
        classes = list(map(int, classes))

    #Tell the user if something wasn't right with the input
    except ValueError:
        print("\n>> Error: could not parse the classes that you passed. Double check that you passed numbers separated by slashes to the --plot_class_iterations option (e.g. 2/6).\n")
        sys.exit()

    #To figure out which iteration this file is, we can find "_it" in the file name first
    #This is only useful for the check below to make sure the right kind of file is passed
    position = filename.find("_it")

    #The iteration number is the 3 values just after "_it"
    #This is placed in a try/except in case the user passes a filename without a "_it" in the name
    try:
        iteration = int(filename[position+3:position+6])
    except ValueError:
        print("\n>> Error: could not find the iteration number in the filename. The file should be similar to \"run_it025_data.star\".\n")
        sys.exit()

    #To figure out how many classes there are, we can read in the file and find 
    #the highest class number i.e. the maximum of the integer list of classes.
    allparticles, metadata = fileparser.getparticles(filename)
    numclasses = max(list(map(int, allparticles["_rlnClassNumber"].tolist())))

    """
    Now that it looks like things have been passed properly, we can generate a list of files
    and parse them one by one.
    """

    print("\n>> Processing iteration 2 to " + str(iteration) + " for " + str(numclasses) + " classes")

    #Use the helper function getiterationlist() to get the list of files to parse
    iterationfilename = getiterationlist(filename)

    """
    The way the function is designed, when the user passes "all" to plot all classes,
    this information is passed as setting the classes to -1.
    """

    #If not plotting all classes, tell the user so
    if -1 not in classes:
        print("\n>> Only plotting classes: " + str(classes))

    """
    The code below goes through each iteration star file, gets the number of particles
    per class, and stores the information in a dataframe to stay organized.
    """

    #Generate an empty dataframe to load with data
    numperclassdf = pd.DataFrame()

    #Loop through each iteration file
    for i in range(len(iterationfilename)):

        #Get the current filename
        iterationfile = iterationfilename[i]

        #Parse the star file for the current iteration
        allparticles, metadata = fileparser.getparticles(iterationfile)

        numperclass = []

        #For each class number, count the number of particles using countqueryparticles()
        #Note that queryexact is set to True here by default in decisiontree.py, which is
        #necessary so that "1" doesn't get confused with "10"
        for c in range(1,numclasses+1):
            numperclass.append(particleplay.countqueryparticles(allparticles, ["_rlnClassNumber"], [str(c)], queryexact, quiet=True))

        #Store the list as a column in the numperclassdf dataframe with the header as the iteration number
        #Set column names to proper iteration number since we are skipping 0 and 1
        numperclassdf[str(i+2)] = numperclass

    #The row numbers in a dataframe start at 0, so we need to increase
    #them by 1 so that the rows properly match the class number
    numperclassdf.index +=1

    #Plot the classes. If classes contained -1, then the user wanted all classes plotted,
    #otherise, just plot the ones that were requested
    for c in range(numclasses):
        #range starts at 0, so the class number is c+1
        classinquestion = c+1
        if -1 in classes:
            ax = numperclassdf.iloc[c].plot(kind='line', legend = True, linewidth = 2, alpha = 0.7)
        elif classinquestion in classes:
            ax = numperclassdf.iloc[c].plot(kind='line', legend = True, linewidth = 2, alpha = 0.7)

    #Set the axis labels
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Particle number")

    #Get the Figure instance to pass to outputfig() for writing to disk
    fig = ax.get_figure()

    #outputfig takes the Figure instance, the file name, and file type (passed by the user)
    outputfig(fig, "Class_distribution", outtype)

"""
This is a helper function for plotclassparts() to generate a list of file names
for all iterations up to the one that was passed. This is an overly complicated
way to do this but works well. Consider simplifying.
e.g. it returns ['run_it002_data.star', 'run_it003_data.star', etc.]
"""
def getiterationlist(filename):
    
    position = filename.find("_it")
    iteration = int(filename[position+3:position+6])

    #Check if this is job was continued at a certain iteration
    if filename.find("_ct") != -1:

        """
        The code below is convoluted but works
        """

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

    #Skip iteration 0 and 1 since the proportions
    #are not informative
    return(iterationfilename[2:])

"""
--plot_orientations
The function below is adapted from Israel Fernandez (PirateFernandez) rln_star_2_mollweide_any_star.py
"""
def plotangledist(particles, outtype):

    """
    AngleRot and AngleTilt are used for the plot.
    list(map(float,list()) is used to turn the list of strings
    into a list of floats
    """
    rot=list(map(float, list(particles["_rlnAngleRot"])))
    tilt=list(map(float, list(particles["_rlnAngleTilt"])))

    #Rotate the tilt angle by 90 degrees
    tilt_m90 = [i -90 for i in tilt]

    #Turn degrees into radians
    rot_rad = np.deg2rad(rot)
    tilt_m90_rad = np.deg2rad(tilt_m90)

    #~needs explanation~
    vertical_rad = np.vstack([tilt_m90_rad, rot_rad])

    #~needs explanation~
    try:
        m = gaussian_kde(vertical_rad)(vertical_rad)

    #It's bad practice to have a naked exception here. Consider getting the exact exception.
    except:
        print("\n>> Error: check the _rlnAngleRot and _rlnAngleTilt columns.\n")
        sys.exit()

    # fig = plt.figure(figsize=(3, 3))
    # plt.hist(rot_rad)
    # outputfig(fig,"rot_rad")

    # fig = plt.figure(figsize=(3, 3))
    # plt.hist(tilt_m90_rad)
    # outputfig(fig,"tilt_m90_rad")

    #Generate the figure instance
    fig = plt.figure(figsize=(3.5, 1.8))

    #Define the plot as a mollweide projection
    ax = plt.subplot(111, projection="mollweide")

    """
    For star files with more than 200,000 particles, the size if the plotted scatter point
    should be 0.1, but that gets to be too small for fewer particles. This equation increases
    the size so that particles in the tens of thousands can still look decent in the plot
    """
    spotsize = -0.000006*len(particles.index)+1.4
    if spotsize < 0.1:
        spotsize = 0.1

    """
    In some cases, an invalid value error is thrown while calculating arcsin for the projection in scatter().
    warnings.catch_warnings allows us to ignore it to keep the terminal output clean.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        #Plot!
        ax.scatter(rot_rad, tilt_m90_rad, cmap="Blues", c=m, s=spotsize, alpha=0.1)

    #Remove the tick labels to make the plot cleaner
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    """
    Draw curved lines at x -120, -60, 60, 120.
    Currently commented out.
    """
    #x_60_rad = [1.047 for i in range(0,7)]
    #x_m60_rad = [-1.047 for i in range(0,7)]
    #x_120_rad = [2.094 for i in range(0,7)]
    #x_m120_rad = [-2.094 for i in range(0,7)]
    #ax.plot(x_60_rad, np.arange(-1.5, 2, 0.5), color='k', lw=1.5, linestyle=':')
    #ax.plot(x_m60_rad, np.arange(-1.5, 2, 0.5), color='k', lw=1.5, linestyle=':')
    #ax.plot(x_120_rad, np.arange(-1.5, 2, 0.5), color='k', lw=1.5, linestyle=':')
    #ax.plot(x_m120_rad, np.arange(-1.5, 2, 0.5), color='k', lw=1.5, linestyle=':')

    """
    Draw vertical and horizontal straight lines as x, y cartesian axes.
    Currently commented out.
    """
    #ax.vlines(0,-1.6,1.6, colors='k', lw=1.5, linestyles=':')
    #ax.hlines(0,-10,10, colors='k', lw=1.5, linestyles=':')

    #########################################################################################################

    #Show color bar

    cbar = plt.colorbar(
            plt.cm.ScalarMappable(
                norm=mpl.colors.Normalize(0, 1), cmap="Blues"
            ), shrink=0.6, pad = 0.1#cax = fig.add_axes([0.92, 0.33, 0.03, 0.38])
        )
    cbar.set_label("Orientation Density")

    #Padding puts some white space around the figure
    plt.tight_layout(pad=0.2)

    #outputfig takes the Figure instance, the file name, and file type (passed by the user)
    outputfig(fig, "Particle_orientations", outtype)

"""
This is the old function to plot angular distributions that I wrote,
it is slower and uglier than plotangledist(), but works as well.
It is left here in case it is helpful for others.
"""
def plotangledist_old(particles, outtype):

    lon=list(map(float, list(particles["_rlnAngleRot"])))
    lat=list(map(float, list(particles["_rlnAngleTilt"])))

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

    #outputfig() takes the Figure instance, the file name, and file type (passed by the user)
    outputfig(fig, "Particle_orientations", outtype)

"""
--plot_class_proportions
"""
def classproportion(particles, columns, query, queryexact, outtype):

    #This is the number of queries that were passed
    totalqueried = len(query)
    
    #Calculating a proportion requires that more than 1 query was passed
    if totalqueried < 2:
        print("\n>> Error: enter at least two queries separated by a slash.\n")
        sys.exit()

    #Use extractparticles() to get the subset of particles that contain the queries since those are
    #the only relevant ones when calculating the proportions
    subsetparticles, totalsubset = particleplay.extractparticles(particles, columns, query, queryexact)

    #If no particles match the queries, then the returned dataframe will be empty, so we can't continue
    if len(subsetparticles.index) == 0:
        print("\n>> Error: no classes seem to contain the desired queries in the specified column.\n")
        sys.exit()

    #To figure out the class numbers, the _rlnClassNumber column is extracted
    #and the set is calculated (i.e. all unique values), and is turned into a list
    classestocheck = list(set(subsetparticles["_rlnClassNumber"]))

    #In order to sort the classes in ascending order, we need to first
    #turn them into integers, sort them, then turn them back to strings
    classestocheck_int = [int(i) for i in classestocheck]
    classestocheck_int.sort()
    classestocheck = [str(i) for i in classestocheck_int]

    print("\n>> There are " + str(len(classestocheck)) + " classes that contain the queries. Checking the proportion of " + str(query) + ".")

    #Initialize a list to store the proportions
    percentparts_lst = []

    #Go class by class and check the proportions
    for c in classestocheck:

        #Get the subset of particles that belong to the class in question
        sub_subsetparticles = subsetparticles[subsetparticles["_rlnClassNumber"] == c]

        totalclasssubsubset = len(sub_subsetparticles)

        percentparts = []

        #Figure out the proportion of each query in that class
        for q in query:

            #The countqueryparticles() does this for us already
            totalclasspartsinsubset = particleplay.countqueryparticles(sub_subsetparticles, columns, [q], queryexact, quiet=True)

            #This is a list of proportions for each query in this class
            percentparts.append(totalclasspartsinsubset*100 / totalclasssubsubset)

        #The list of proportions is stored in this list of lists for each class
        percentparts_lst.append(percentparts)

    for i,c in enumerate(classestocheck):

        print("\n  Class " + c)
        print("  --------")

        for j,q in enumerate(query):

            print("  · " + q + ": " + str(round(percentparts_lst[i][j],1)) + "%")

    print("\n")

    """
    Now that we've figured out the proportions, we want to plot the result as
    a stacked bar graph. One way to do this is to turn the list of proportions
    into a cumulative one, such that when the bar graphs are plotted on top of each
    other, it looks like a stacked bar graph.
    """

    percentparts_cumulative = []

    for c in range(len(classestocheck)):

        #Use the accumulate from itertools to turn the list of percentages into a cumulative list
        #and append it to the list of lists: percentparts_cumulative
        percentparts_cumulative.append(list(accumulate(percentparts_lst[c])))


    """
    This list is ordered by class, but in order to plot it properly, it needs
    to be listed by query. The for loop below turns [[i,j], [k,z]] into [[i,k], [j,z]]
    """

    percentparts_reordered = []
    for q in range(totalqueried):
        percentparts_reordered.append([item[q] for item in percentparts_cumulative])

    """
    The rest of the function is plotting the cumulative proportions for each
    class properly as a "stacked" bar graph
    """

    #This is arbitrary but seems to work well to size the figure appropriately
    #according to how many classes there are
    if len(classestocheck)/3.5 < 6:
        figwidth = 6
    else:
        figwidth = len(classestocheck)/3.5

    #Generate a figure instance
    fig = plt.figure(figsize=(figwidth,5))

    """
    Since the values per class were made to be cumulative, these will look like stacked bar graphs.
    This has to be reversed since the large values need to go first, or else they will cover the 
    small values.
    """
    for q in list(reversed(range(totalqueried))):
        plt.bar(classestocheck, percentparts_reordered[q], 0.32) #0.32 width seems to work well

    #The legend is the queries (reversed to match above)
    plt.legend(list(reversed(query)), bbox_to_anchor=(1.04,1))

    plt.ylabel('Percent of Particles')
    plt.xlabel('Class Number')
    plt.tight_layout()
    
    #outputfig takes the Figure instance, the file name, and file type (passed by the user)
    outputfig(fig, "Class_proportion", outtype)

"""
--plot_coordinates
"""
def comparecoords(file1parts, file2parts, numtoplot, circlesize):

    #This is arbitrary, but seems to get close to the real values.
    #Consider getting this accurate.
    circlesize = (3.14*circlesize/11)**2

    #Check that the micrograph column exists
    if "_rlnMicrographName" not in file1parts:
        print("\n>> Error: the star file does not have a _rlnMicrographName column.\n")
        sys.exit()

    #It makes this easier later if we remove the path to the micrograph name
    #(i.e. everything before the last '/'). The original micrograph name is preserved
    #in _rlnMicrographNameOriginal
    file1parts["_rlnMicrographNameOriginal"] = file1parts["_rlnMicrographName"]
    file1parts["_rlnMicrographName"] = file1parts["_rlnMicrographName"].str.split('/').str[-1]

    #Generate a groupby object that is grouped by micrographs since we want to
    #treat each micrograph independently
    file1mics = file1parts.groupby(["_rlnMicrographName"])

    #Check that the coordinate columns exist
    if "_rlnCoordinateX" not in file1parts or "_rlnCoordinateY" not in file1parts:
        print("\n>> Error: the star file does not have a the coordinate columns.\n")
        sys.exit()

    #get_loc finds the index of the column for retrieval later down the function
    #Consider simplifying this such that the columns are called directly.
    file1originalmics = file1parts.columns.get_loc("_rlnMicrographNameOriginal")+1
    file1xloc = file1parts.columns.get_loc("_rlnCoordinateX")+1
    file1yloc = file1parts.columns.get_loc("_rlnCoordinateY")+1

    #Do the same for the second star file if it has values. The original micrograph names don't 
    #need to be preserved.
    if not file2parts.empty:
        
        if "_rlnMicrogrpahName" not in file2parts:
            print("\n>> Error: the second star file does not have a _rlnMicrographName column.\n")
            sys.exit()

        file2parts["_rlnMicrographName"] = file2parts["_rlnMicrographName"].str.split('/').str[-1]

        file2mics = file2parts.groupby(["_rlnMicrographName"])

        #Check that the coordinate columns exist
        if "_rlnCoordinateX" not in file2parts or "_rlnCoordinateY" not in file2parts:
            print("\n>> Error: the second star file does not have a _rlnMicrographName column.\n")
            sys.exit()

        file2xloc = file2parts.columns.get_loc("_rlnCoordinateX")+1
        file2yloc = file2parts.columns.get_loc("_rlnCoordinateY")+1

    #Generate a figure instance
    fig = plt.figure()

    """
    This count is only useful for when we generate a pdf, since we only want to generate
    it on the first iteration. This can't be done outside the for loop in case the loop crashes
    (e.g. if the micrograph .mrc doesn't exist).
    Consider revising such that a micrograph .mrc is checked first before running the loop
    """

    count=0

    #Loop through the micrographs since it's a groupby object
    #Consider revising with "for idm, file1mic in file1mics" to avoid
    #having to use get_loc above.
    for file1mic in file1mics:

        count+=1

        #Check if the second star file has particles in this micrograph
        #We will store this information in a "skipflag" True/False variable
        if not file2parts.empty:
            try:
                 #If get_group succeeds, then it exists, skipflag is False
                file2mic = file2mics.get_group(file1mic[0])
                skipflag = False

            #If it fails, skipflag is True
            except KeyError:
                skipflag = True
        
        #If there was no second file to begin with, skipflag is True
        else:
            skipflag = True
            
        #Since we didn't expand the file1mics groupby object, file1mic[0] is the micrograph name
        mic = file1mic[0] #.split("/")[-1]
        
        #Generate the figure instance for this micrograph
        fig, ax = plt.subplots(figsize=(22.52,16.36))
        
        #Since we didn't expand the file1mics groupby object, file1mic[1] contains the data for
        #that micrograph. This can be iterated through with.itertuples()
        for file1part in file1mic[1].itertuples():

            #We found the location of the CoordinateX and CoordinateY columns above
            #These need to be turned to floats since they come in as strings
            x1 = float(file1part[file1xloc])
            y1 = float(file1part[file1yloc])

            #These are now plotted normally with the arbitrary circlesize calculated above
            plt.scatter(x1,y1, color='red', facecolors='none', s=circlesize, alpha=0.7, linewidth = 4)

        #If there is a second star file and there are particles on this micrograph, do the same
        if not skipflag:

            for file2part in file2mic.itertuples():

                x2 = float(file2part[file2xloc])
                y2 = float(file2part[file2yloc])

                #The circle size is made slightly bigger so you can see it
                plt.scatter(x2,y2, color='blue', facecolors='none', s=circlesize, alpha=0.7, linewidth = 3.5, linestyle='dashed')

        #We need the micrograph with the full path to source it
        themic = file1part[file1originalmics]

        #Check if it exists. If it is a relative path, you need to run the command from the right location
        if not os.path.isfile(themic):
            print("\n>> Error: the micrograph " + themic + " does not exist. Are you running starparser from the right directory?\n")
            sys.exit()
        else:
            #We need to open a pdf to start writing to it, but only once in the beginning
            if count == 1:
                try:
                    pdf = PdfPages('Coordinates.pdf')
                #Consider fixing this naked exception
                except:
                    print("\n>> Error: could not save to Coordinates.pdf. Is it still open?\n")
                    sys.exit()

            """
            Below is the minimal set of code required for reading in an mrc file such
            that it can be plotted with plt.imshow().
            The tricky bit is reading the header properly.
            """

            header_dtype = np.dtype(
                [('head1', '10int32'), ('head2', '6float32'), ('axisOrientations', '3int32'), ('minMaxMean', '3int32'),
                 ('extra', '32int32')])
            header = np.fromfile(themic, dtype=header_dtype, count=1)
            head1 = header['head1'][0]
            extra = header['extra'][0][1]
            dataSize = head1[0:3]
            dataSize = dataSize[::-1]
            mrcType = head1[3]
            if mrcType == 0:
                dataType = np.int8
            elif mrcType == 1:
                dataType = np.int16
            elif mrcType == 2:
                dataType = np.float32
            elif mrcType == 6:
                dataType = np.uint16
            num0 = int(np.prod(dataSize, dtype=np.uint64))
            with open(themic) as f:
                data1 = np.fromfile(f, dtype=dataType, count=num0, offset = 1024+extra)
            data1 = data1.reshape(dataSize)
            data1 = data1[0,:,:]

            #Once the data has been extracted, imshow() can be used to display it on the same coordinate system as the scatter
            #vmin and vmax are used to adjust the contrast. I have it set to 10% and 90%, but this can be adjusted here.
            plt.imshow(data1, 'gray', origin='lower', vmin=np.percentile(np.ndarray.flatten(data1), 10), vmax=np.percentile(np.ndarray.flatten(data1), 90))

        #The lines below just dress up the plot
        plt.title(file1part[file1originalmics], fontsize = 20)
        plt.xlabel("Pixels", fontsize = 24)
        plt.ylabel("Pixels", fontsize = 24)
        plt.xticks(fontsize = 24)
        plt.yticks(fontsize = 24)
        plt.tight_layout()

        #The figure instance is saved to the pdf
        pdf.savefig(fig)

        #The plots are closed to not exhaust the memory in case
        #many plots will be generated
        plt.close('all')

        #If we've plotted the requested amount, we can exit the loop
        if count == numtoplot:
            break

    #The pdf must be closed properly once finished
    pdf.close()

    print("\n-->> Output figure to Coordinates.pdf\n")

"""
This is a helper function to write figure instances to disk from the functions above.
This helps in case I want to change the default dpi in the future.
"""
def outputfig(fig, name, outtype):
    
    fig.savefig(name + "." + outtype, dpi=300)
    print("\n-->> Output figure to " + name + "." + outtype + ".\n")

