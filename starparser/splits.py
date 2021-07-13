from starparser import particleplay
from starparser import fileparser
import sys

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

def splitbyoptics(particles,metadata,queryexact):
    print("")
    for n,o in zip(metadata[2]["_rlnOpticsGroup"],metadata[2]["_rlnOpticsGroupName"]):
        subsetoptics, subsetopticslength = particleplay.extractparticles(particles,["_rlnOpticsGroup"],[n],queryexact)
        newmetadata = [metadata[0], metadata[1], metadata[2][metadata[2]["_rlnOpticsGroupName"] == o], metadata[3], metadata[4]]
        print(">> Optics group " + str(n) + " has " + str(subsetopticslength) + " particles.")
        fileparser.writestar(subsetoptics, newmetadata, o+".star", False)

def splitbyclass(particles,metadata,queryexact,relegateflag):
    classes = list(set(particles["_rlnClassNumber"]))   
    classes = sorted(list(map(int, classes)))
    for c in classes:
        classparticles, classparticleslength = particleplay.extractparticles(particles,["_rlnClassNumber"],[str(c)],queryexact)
        print("\n>> Class " + str(c) + " has " + str(classparticleslength) + " particles.")
        fileparser.writestar(classparticles, metadata, "Class_"+str(c)+".star", relegateflag)
    print("")