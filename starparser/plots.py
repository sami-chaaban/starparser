import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import sys
import numpy as np
import os
import scipy
from scipy.stats import gaussian_kde

from starparser import fileparser
from starparser import particleplay

def plotcol(particles, column, outtype):

    if len(particles.index) == 0:
        print("\n>> Error: no particles to plot.\n")
        sys.exit()
    
    particles[column] = pd.to_numeric(particles[column], downcast="float")

    numparticles = len(particles.index)

    ax = particles[column].plot.hist(bins='fd')
    ax.set_xlabel(column[4:])
    
    fig = ax.get_figure()
    outputfig(fig, column[4:], outtype)

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
    
def plotclassparts(filename, classes, queryexact, outtype):
    
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
    allparticles, metadata = fileparser.getparticles(filename)
    numclasses = max(list(map(int, allparticles["_rlnClassNumber"].tolist())))
    iterationfilename = getiterationlist(filename)
    
    print("\n>> Processing iteration 2 to " + str(iteration) + " for " + str(numclasses) + " classes.")
    if -1 not in classes:
        print("\n>> Only plotting classes " + str(classes) + ".")

    numperclassdf = pd.DataFrame()

    for i in range(len(iterationfilename)):
        iterationfile = iterationfilename[i]
        allparticles, metadata = fileparser.getparticles(iterationfile)
        numperclass = []
        for c in range(1,numclasses+1):
            numperclass.append(particleplay.countqueryparticles(allparticles, ["_rlnClassNumber"], [str(c)], queryexact, True))
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
    outputfig(fig, "Class_distribution", outtype)

def plotangledist_old(particles, outtype):

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

    outputfig(fig, "Particle_orientations", outtype)

def plotangledist(particles, outtype):

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

    outputfig(fig, "Particle_orientations", outtype)

def classproportion(particles, columns, query, queryexact, outtype):

    totalqueried = len(query)
    
    if totalqueried < 2:
        print("\n>> Error: enter at least two queries separated by a slash.\n")
        sys.exit()

    subsetparticles, totalsubset = particleplay.extractparticles(particles, columns, query, queryexact)

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
            totalclasspartsinsubset = particleplay.countqueryparticles(sub_subsetparticles, columns, [q], queryexact, True)
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
    
    outputfig(fig, "Class_proportion", outtype)

def comparecoords(file1parts,file2parts,numtoplot):

    file1parts["_rlnMicrographNameOriginal"] = file1parts["_rlnMicrographName"]
    file1parts["_rlnMicrographName"] = file1parts["_rlnMicrographName"].str.split('/').str[-1]

    file1mics = file1parts.groupby(["_rlnMicrographName"])
    file1originalmics = file1parts.columns.get_loc("_rlnMicrographNameOriginal")+1
    file1xloc = file1parts.columns.get_loc("_rlnCoordinateX")+1
    file1yloc = file1parts.columns.get_loc("_rlnCoordinateY")+1
    file1nameloc = file1parts.columns.get_loc("_rlnImageName")+1
    if not file2parts.empty:
        file2parts["_rlnMicrographName"] = file2parts["_rlnMicrographName"].str.split('/').str[-1]
        file2mics = file2parts.groupby(["_rlnMicrographName"])
        file2xloc = file2parts.columns.get_loc("_rlnCoordinateX")+1
        file2yloc = file2parts.columns.get_loc("_rlnCoordinateY")+1

    fig = plt.figure()

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

    count=0

    for file1mic in file1mics:

        if numtoplot != -1:
            count+=1

        skipflag = False
        try:
            file2mic = file2mics.get_group(file1mic[0])
        except:
            skipflag = True
            
        mic = file1mic[0] #.split("/")[-1]
        
        fig, ax = plt.subplots(figsize=(22.52,16.36))
        
        for file1part in file1mic[1].itertuples():
            x1 = float(file1part[file1xloc])
            y1 = float(file1part[file1yloc])
            plt.scatter(x1,y1, color='red', facecolors='none', s=80, alpha=0.7, linewidth = 4)

        if not skipflag and not file2parts.empty:
            for file2part in file2mic.itertuples():
                x2 = float(file2part[file2xloc])
                y2 = float(file2part[file2yloc])
                plt.scatter(x2,y2, color='blue', facecolors='none', s=250, alpha=0.7, linewidth = 3.5)

        themic = file1part[file1originalmics]
        if not os.path.isfile(themic):
            print("\n>> Error: the micrograph " + themic + " does not exist. Are you running starparser from the right directory?\n")
            sys.exit()
        else:
            if count == 1:
                try:
                    pdf = PdfPages('Coordinates.pdf')
                except:
                    print("\n>> Error: could not save to Coordinates.pdf. Is it still open?\n")
                    sys.exit()

            #Plot mrc:
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
            plt.imshow(data1, 'gray', origin='lower', vmin=np.percentile(np.ndarray.flatten(data1), 10), vmax=np.percentile(np.ndarray.flatten(data1), 90))

        plt.title(file1part[file1originalmics], fontsize = 20)
        plt.xlabel("Pixels", fontsize = 24)
        plt.ylabel("Pixels", fontsize = 24)
        plt.xticks(fontsize = 24)
        plt.yticks(fontsize = 24)
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close('all')

        if count == numtoplot:
            break

    pdf.close()

    print("-->> Output figure to Coordinates.pdf\n")

def outputfig(fig, name, outtype):
    
    fig.savefig(name + "." + outtype, dpi=300)
    print("\n-->> Output figure to " + name + "." + outtype + ".\n")

