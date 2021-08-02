import sys
import pandas as pd

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

    if any("_rln" in i for i in items):
        print("\n>> Error: something went wrong during parsing. Are there more than two data tables?\n")
        sys.exit()

    totalcolumns = len(headers)

    items_lst = [items[x:x+totalcolumns] for x in range(0, len(items), totalcolumns)]

    itemspd = pd.DataFrame(items_lst, columns = headers)

    return(itemspd)

def getparticles(filename):

    print("\n>> Reading " + filename)
    
    file = open(filename,mode='r')
    starfile = file.read()
    file.close()

    try:

        # import time
        # tic = time.perf_counter()

        version, opticsheaders, optics, particlesheaders, particles, tablename = parsestar(starfile)

        # toc = time.perf_counter()
        # print(f"parsestar took {toc - tic:0.4f} seconds")

    except:

        print("\n>> Error: a problem was encountered when trying to parse " + filename + ".\n")
        sys.exit()
    
    alloptics = makepandas(opticsheaders, optics)
    allparticles = makepandas(particlesheaders, particles)
    
    if len(particlesheaders) != len(allparticles.columns):
        print("\n>> Error: something went wrong when parsing " + filename + ".\n")
        sys.exit()
    
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

def writestar(particles, metadata, outputname, relegate=False):

    if len(particles.index) == 0:
        print("\n>> Error: no particles to output.\n")
        sys.exit()
    
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