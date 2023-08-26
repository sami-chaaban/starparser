import sys
import pandas as pd

def getparticles(filename):

    """
    This is the entry point. The file is read, passed to parsestar() to figure out where the tables are,
    and that information is passed to makepandas() to generate dataframes.
    """
    
    #Get the data from the star file.
    file = open(filename,mode='r')
    starfile = file.read()
    file.close()

    #The try/except used here is in case the star file is wonky.
    try:

        #The commented timer lines below are used to test different ways of parsing the star file to eventually find the fastest method.

        # import time
        # tic = time.perf_counter()

        #The file is parsed by parsestar() to figure out where the relevant information lies.
        version, opticsheaders, optics, particlesheaders, particles, tablename = parsestar(starfile)

        # toc = time.perf_counter()
        # print(f"\nparsestar took {toc - tic:0.4f} seconds")

    #It is generally bad practice to have a naked exception here, but it should be fine for basic use.
    except:

        print("\n>> Error: a problem was encountered when trying to parse " + filename + ".\n")
        sys.exit()

    #Make a dataframe out of the values and headers.
    alloptics = makepandas(opticsheaders, optics)
    allparticles = makepandas(particlesheaders, particles)
    
    #Check that the number of columns in the generated dataframe matches the number of headers, otherwise something must have gone wrong.
    if len(particlesheaders) != len(allparticles.columns):

        print("\n>> Error: something went wrong when parsing " + filename + ".\n")
        sys.exit()
    
    #Aggregate the non-particles data into a metadata list for simplicity.
    metadata = [version,opticsheaders,alloptics,particlesheaders,tablename]

    return(allparticles, metadata)


def parsestar(starfile):

    """
    Assumption: there are two tables with data; the first is assumed to be the optics table.
    This function gets the star file information from getparticles() and the result is passed to makepandas().
    """

    #Generate a list of lines from the star file. Anything that is tab or space delimited will occupy different indices in the list
    starfilesplit = starfile.split()

    """
    We will make a short version of starfilesplit to use while figuring out the headers
    This increases the speed of parsing significantly, especially for large files
    The first 10000 lines should be enough.
    """
    if len(starfilesplit) > 10000:
        starfilesplit_test = starfilesplit[0:10000]
    else:
        starfilesplit_test = starfilesplit

    """
    #Version
    The version header is not always present
    """

    #Check if "# version xxxx" exists
    try:
        
        #Try getting the index for the word "version"
        versionindex = starfilesplit_test.index("version")
        
        #If no exception was thrown, the index was found, so there is a version header
        #This flag will be useful later
        versionexist = True

        #We want the "#" before "version" up to the "30001" after
        version = starfilesplit_test[versionindex-1:versionindex+2]

    #If "version" doesn't exist, a ValueError exception will be thrown
    except ValueError:

        #This flag will be useful later
        versionexist = False

        #We'll make up a version header in this case
        version = ["#", "version", "30001"]

    """
    #Optics table headers
    """

    #Data tables start with "loop_". The first data table is the optics table
    opticsstart = starfilesplit_test.index("loop_") + 1

    #The column names (i.e. table headers) for the optics table are stored here
    opticstableheaders = []

    #Loop through every other value from loop_ onwards, since the values will be
    #"[#X, _rlnColumnName, #Y, _rlnNextColumnName,...]"
    for i,n in enumerate(starfilesplit_test[opticsstart::2]):
        
        #Once you hit a value that doesn't start with an underscore, the headers have ended
        if n[0] != "_":

            #since "i" comes from an enumerate variable, it must be multiplied by two
            #to accomodate the fact that we were looping every two values
            opticsheaderend = opticsstart + i*2

            #We can get out of the for loop now
            break

        #Keep adding the header names as long as one is found
        opticstableheaders.append(n)

    """
    #Version
    """

    #The same logic as above

    try:
        starfilesplit_test[opticsheaderend:].index("version")
        versionexist = True
    except ValueError:
        versionexist = False

    """
    #Table Name
    """

    """
    For the second data table, we want to know what kind of table it is
    e.g. data_particles
    """

    if versionexist:
        opticsdataend = starfilesplit_test[opticsheaderend:].index("#") + opticsheaderend
        tablename = starfilesplit_test[opticsdataend+3]
    else:
        opticsdataend = starfilesplit_test[opticsheaderend:].index("loop_") + opticsheaderend - 1
        tablename = starfilesplit_test[opticsdataend]

    optics = starfilesplit_test[opticsheaderend:opticsdataend]

    """
    #Particles Header
    """

    #Same logic as above

    particlesstart = starfilesplit_test[opticsdataend:].index("loop_") + 1 + opticsdataend

    particlestableheaders = []
    for i,n in enumerate(starfilesplit_test[particlesstart::2]):
        if n[0] != "_":
            particlesheaderend = particlesstart + i*2
            break
        particlestableheaders.append(n)

    """
    #Particles
    """

    #The remainder of the data is the particles
    #They will get parsed properly in makepandas()

    particles = starfilesplit[particlesheaderend:]

    return(version,opticstableheaders,optics,particlestableheaders,particles,tablename)

def makepandas(headers,items):

    """
    The star file data is initially parsed with parsestar() before this function can generate a dataframe.
    """

    #If there is another data table, then _rln will be found improperly in the particles data, which will not work.
    if any("_rln" in i for i in items):
        print("\n>> Error: something went wrong during parsing. Are there more than two data tables?\n")
        sys.exit()

    #Calculate the number of columns, since this will be used to properly split the data into lines that belong to each particle.
    totalcolumns = len(headers)

    """
    These are the slowest parts of the code. Consider making more efficient.
    """

    #Split the list given the number of columns expected for each particle
    items_lst = [items[x:x+totalcolumns] for x in range(0, len(items), totalcolumns)]

    #Generate a pandas dataframe
    itemspd = pd.DataFrame(items_lst, columns = headers)

    return(itemspd)


def getparticles_dummyoptics(filename):

    """
    This is similar to getparticles(), but inserts a fake optics table so that parsing downstream is unchanged.
    """

    file = open(filename,mode='r')
    starfile = file.read()
    file.close()

    #This is the fake optics table
    tempinsertion = "\n# version 30000\n\ndata_optics\n\nloop_\n_rlnOpticsGroupName #1\n_rlnOpticsGroup #2\n_rlnVoltage #3\n_rlnImagePixelSize #4\nopticsGroup1\t1\t300.000000\t1.000000\n\n\n# version 30000\n\ndata_images\n\n"

    #The fake optics table must be inserted just before loop_.
    looploc = starfile.find("loop_")

    #Append the optics table
    starfile = tempinsertion + starfile[looploc:]

    #Parse the file now as with getparticles() and generate dataframes.
    version, opticsheaders, optics, particlesheaders, particles, tablename = parsestar(starfile)
    alloptics = makepandas(opticsheaders, optics)
    allparticles = makepandas(particlesheaders, particles)
    metadata = [version,opticsheaders,alloptics,particlesheaders,tablename]

    return(allparticles, metadata)


def writestar(particles, metadata, outputname, relegate=False):

    """
    This method writes out a star file from dataframes.
    The relegate variable is used to see if an optics table should not be written.
    """

    #Sometimes, data mining results in a void particle set, which is not useful to write out.
    if len(particles.index) == 0:
        print("\n>> Error: no particles to output.\n")
        sys.exit()
    
    #Open the file to write to. This is closed once all the data has been written (with output.close()).
    output = open(outputname,"w")
    
    #Start with an empty line
    output.write('\n')

    #Get the version from the metadata aggregate list
    version = metadata[0]

    #Write the version values
    for t in version:
        output.write(t)
        output.write(' ')
    output.write('\n\n')
    
    #For Relion >3.0, the optics table should be written (i.e. relegate=False).
    if not relegate:

        #Write the generic headers for the optics data
        output.write('data_optics\n\n')
        output.write('loop_')
        
        #Get the optics headers from the metadata aggregate list
        opticsheaders = metadata[1]

        #Initialize a count variable to increment the column numbers
        count=1

        #Write out the optics header information, interspersing #N given the column number
        for p in opticsheaders:
            output.write('\n')
            output.write(p)
            output.write(" #"+str(count))
            count += 1
        output.write('\n')

        #Get the optics data from the metadata aggregate list
        optics = metadata[2]

        #Since the optics data is a dataframe, the to_csv function can be used to write out the data.
        optics.to_csv(output, header=None, index=None, sep='\t', mode='a')

        #Write the version values again before the next table
        output.write('\n\n')
        for t in version:
            output.write(t)
            output.write(' ')
            
        output.write('\n\n')

    #Get the table name from the metadata aggregate list (e.g. data_particles) and write it.
    output.write(metadata[4])
    output.write('\n\n')
    output.write('loop_')

    #Get the paritlce headers from the metadata aggregate list and write them as above.
    headers = metadata[3]
    count=1
    for p in headers:
        output.write('\n')
        output.write(p)
        output.write(" #"+str(count))
        count += 1

    output.write('\n')

    #Write out the particles data from the dataframe as above.
    particles.to_csv(output, header=None, index=None, sep='\t', mode='a')

    #Close the file
    output.close()

    print("-->> Output star file: " + outputname + "\n")

"""
The following is an old version of parsestar
It is left here in case it is useful to others
"""
def parsestar_old(starfile):

    """
    This is a quite inefficient way of parsing a star file but does the job.
    The assumption below is that the star file has version headers that look like "# version xxxxx".

    This function gets the star file information from getparticles() and the result is passed to the makepandas().
    """

    #Generate a list of lines from the star file. Anything that is tab or space delimited will occupy different indices in the list
    starfilesplit = starfile.split()

    #This variable will be used to determine at which index the optics data ends
    #It is initialized as 0 in case the end of the optics data is not found (see the check below)
    opticsstop = 0

    #Check from after the fist version header to index 2000 (arbitrary), that should be enough to find things
    for i in range(4,2000):
        
        #Check if you reached the next version header, this means you've passed the optics data
        if starfilesplit[i] == '#': 
            
            #We've found the index of the end of the next version header which means that the optics data has also ended.
            opticsstop = i
            break
            
    #Check if the opticsstop variable didn't change, which means something went wrong when parsing
    if opticsstop == 0:
        
        print('\n>> Error: Could not find the end of the optics table.\n')
        sys.exit()

    #For finding the end of the particles table headers
    particlesstop = 0 

    #For finding the end of the optics table headers
    opticstablestop = 0
    
    #Now that we know where the optics table ends, we can use that as an end to searching for the optics table
    #Search every two indices since table headers have two values (i.e. _rlnColumnName #1).
    for i in range(5,opticsstop,2):
        
        #Optics table headers start with _, so when it doesn't happen, we've reached the end of the table headers
        if starfilesplit[i][0] != "_": 
        
            #We've found the index number of the end of the optics table headers
            opticstablestop = i
            break

    #Now we can look for the particles table starting at the end of the optics table.
    #Search every two indces since the particle table headers have two values.
    for i in range(opticsstop+5,2000,2):

        #As above, if you don't find a _, you've reached the end of the table header.
        if starfilesplit[i][0] != "_":
            
            #We've found the index number of the end of the particle table headers.
            particlesstop = i
            break

    #Check if the particlesstop variable didn't change, which means something went wrong when parsing
    if particlesstop == 0:

        print('\n>> Error: Could not find the end of the particles table.\n')
        sys.exit()


    """
    Now that we've fond all the relevant indices, we can use those to parse starfilesplit.
    """

    #The version header is the first three indices (i.e. # version xxxxx)
    version = starfilesplit[0:3]

    #The optics table starts from afte the version header to opticstablestop
    opticstable = starfilesplit[3:opticstablestop]
    
    #We will parse the optics data (i.e. the opticstable list) to extract the headers
    opticstableheaders = []

    #Every two values is the column name (i.e. _rlnColumnName and skipping #1). The [1:] is to avoid the first line in the header, which is "data_optics".
    for m in opticstable[::2][1:]: 
        opticstableheaders.append(m)

    #The optics values start from the end of the optics table to the end of the optics data
    optics = starfilesplit[opticstablestop:opticsstop]

    #The table name for the particles table is the value just after the optics table and just before the particles table (e.g. data_particles).
    tablename = starfilesplit[opticsstop+3]

    #The particles table starts just after the optics data to the end of the particles table.
    particlestable = starfilesplit[opticsstop+3:particlesstop]
    
    #As above, we will parse the particles data (i.e. the particlestable list) to extract the headers
    particlestableheaders = []

    #Every two values is the column name (i.e. _rlnColumnName and skipping #1). The [1:] is to avoid the first line in the header(e.g. "data_particles").
    for m in particlestable[::2][1:]: 
        particlestableheaders.append(m)

    #All the particles data starts after the end of the particles.
    particles = starfilesplit[particlesstop:]

    #The optics data and particles data will get split properly and made into a dataframe with makepandas()
    return(version,opticstableheaders,optics,particlestableheaders,particles,tablename)