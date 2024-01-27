import pandas as pd
import sys

"""
--remove_column
"""
def delcolumn(particles, columns, metadata):
    
    """
    With dataframes, stating dataframe1 = dataframe2 only creates
    a reference. Therefore, we must create a copy if we want to leave
    the original dataframe unmodified.
    """
    nocolparticles = particles.copy()
    
    #Loop through each passed column to delete them
    for c in columns:

        #Check if the column doesn't exist.
        #Consider doing the check in decisiontree.py
        if c not in nocolparticles:
            print("\n>> Error: the column \"" + c + "\" does not exist.\n")
            sys.exit()

        """
        The .drop can be used to drop a whole column.
        The "1" tells .drop that it is the column axis that we want to drop
        inplace means we want the dataframe to be modified instead of creating an assignment
        """
        nocolparticles.drop(c, axis=1, inplace=True)

        #We nead to remove that column header too. The heads are the third
        #metadata (i.e. metadata[3])
        metadata[3].remove(c)
    
    return(nocolparticles, metadata)

"""
--swap_columns
"""
def swapcolumns(original_particles, swapfrom_particles, columns):

    #First, verify that there are the same number of particles in both files
    #Consider placing this in decisiontree.py
    if len(original_particles.index) != len(swapfrom_particles.index):
        print("\n>> Error: the star files don't have the same number of particles: " + str(len(original_particles.index)) + " vs " + str(len(swapfrom_particles.index)) + ".\n")
        sys.exit()
    
    """
    With dataframes, stating dataframe1 = dataframe2 only creates
    a reference. Therefore, we must create a copy if we want to leave
    the original dataframe unmodified.
    """
    swappedparticles = original_particles.copy()
    
    #Loop through the columns
    for c in columns:
        #Check that the column exists in both files
        if c not in original_particles:
            print("\n>> Error: the column \"" + c + "\" does not exist in the original star file.\n")
            sys.exit()
        if c not in swapfrom_particles:
            print("\n>> Error: the column \"" + c + "\" does not exist in the second star file.\n")
            sys.exit()

        """
        We will remove the column then insert the new one
        Therefore, e need to know what the index of the column
        """

        #Get the column index
        columnindex = original_particles.columns.get_loc(c)

        #Remove the column
        """
        The .drop can be used to drop a whole column.
        The "1" means the column axis and inplace means the dataframe
        should be modified instead of creating an assignment
        """
        swappedparticles.drop(c,axis=1,inplace=True)

        """
        Insert the new column in the right index using .insert()
        The function takes a list, so we generate a list of values of
        the new column with .values.tolist()
        """
        swappedparticles.insert(columnindex, c, swapfrom_particles[c].values.tolist())
    
    return(swappedparticles)

"""
--operate
"""
def operate(particles,column,operator,value):

    """
    If we are applying operations, the column must contain numbers.
    We can check that this is the case with a try/except.
    """
    try:
        #to_numeric allows us to change all values of a column to floats
        particles[column] = pd.to_numeric(particles[column], downcast="float")
    #If this didn't work, then they probably weren't numbers
    except ValueError:
        print("\n>> Error: Could not interpret the values in " + column + " as numbers.\n")
        sys.exit()

    """
    Column operations are simple with dataframes
    """

    if operator == "multiply":
        print("\n>> Multiplying all values in " + column + " by " + str(value) + ".")
        particles[column] = particles[column] * value

    elif operator == "divide":
        print("\n>> Dividing all values in " + column + " by " + str(value) + ".")
        particles[column] = particles[column] / value

    elif operator == "add":
        print("\n>> Adding " + str(value) + " to all values in " + column + ".")
        particles[column] = particles[column] + value

    elif operator == "subtract":
        print("\n>> Subtracting " + str(value) + " from all values in " + column + ".")
        particles[column] = particles[column] - value

    return(particles)

"""
--operate_columns
"""
def operatecolumns(particles,column1,column2,newcolumn,operator,metadata):

    """
    If we are applying operations, the column must contain numbers.
    We can check that this is the case with a try/except.
    """
    try:
        #to_numeric allows us to change all values of a column to floats
        particles[column1] = pd.to_numeric(particles[column1], downcast="float")

    #If this didn't work, then they probably weren't numbers
    except ValueError:
        print("\n>> Error: Could not interpret the values in " + column1 + " as numbers.\n")
        sys.exit()

    #Repeat for the second column
    try:
        particles[column2] = pd.to_numeric(particles[column2], downcast="float")
    except ValueError:
        print("\n>> Error: Could not interpret the values in " + column2 + " as numbers.\n")
        sys.exit()


    """
    Column operations are simple with dataframes
    """

    if operator == "multiply":
        print("\n>> Multiplying " + column1 + " by " + column2 + " and storing the result in " + newcolumn + ".")
        particles[newcolumn] = particles[column1] * particles[column2]

    elif operator == "divide":
        print("\n>> Dividing  all values in " + column1 + " by " + column2 + " and storing the result in " + newcolumn + ".")
        particles[newcolumn] = particles[column1] / particles[column2]

    elif operator == "add":
        print("\n>> Adding " + column2 + " to all values in " + column1 + " and storing the result in " + newcolumn + ".")
        particles[newcolumn] = particles[column1] + particles[column2]

    elif operator == "subtract":
        print("\n>> Subtracting " + column2 + " from all values in " + column1 + " and storing the result in " + newcolumn + ".")
        particles[newcolumn] = particles[column1] - particles[column2]

    #Since the new column is added to the end of the dataframe
    #We need to make a new header, which is in metadata[3]
    metadata[3].append(newcolumn)

    return(particles, metadata)

"""
--list_column
"""
def writecol(particles, columns):
    
    #Initialize a list to store the names of the 
    #files that were generated to tell the user later
    outputs = []
    
    #Loop through the columns
    for c in columns:
        
        #It's easier to write values when they are a list,
        #This is easily done with .tolist()
        tosave = particles[c].tolist()
        
        #We remove the _rln from the column name and append .txt
        outputname = c[4:] + ".txt"

        #Write this name to tell the user later that this was written
        outputs.append(outputname)
        
        #Open a file to write to
        output = open(outputname,"w")
        
        #Loop through the values in the list
        for s in tosave:

            #Write the value
            output.write(s)

            #Write a new line
            output.write("\n")
        
        #The file must be closed once finished writing
        output.close()
    
    return(outputs)

"""
--replace_column
"""
def replacecolumn(particles,replacecol,newcol):

    """
    We will remove the column then insert the new one
    Therefore, e need to know what the index of the column
    """

    #Get the column index
    columnindex = particles.columns.get_loc(replacecol)

    #Remove the column
    """
    The .drop can be used to drop a whole column.
    The "1" means the column axis and inplace means the dataframe
    should be modified instead of creating an assignment
    """
    particles.drop(replacecol, axis=1, inplace=True)

    #Insert the new column in the right index using .insert()
    #Since newcol comes in as a list, we don't have to modify it
    particles.insert(columnindex, replacecol, newcol)

    return(particles)

"""
--copy_column
"""
def copycolumn(particles,sourcecol,targetcol,metadata):

    #Check if the column name to copy to exists, if not
    #a new one is created to store the values
    if targetcol not in particles:

        """
        Here we are just telling the user that a new column will be made
        and making a new metadata header. We don't have to create the new column
        since pandas will make it for if it doesn't exist in the line below
        particles[targetcol] = particles[sourecol]
        """
        print("\n>> Creating a new column: " + targetcol + ".")
        metadata[3].append(targetcol)

    else:
        print("\n>> Replacing values in " + targetcol + " with " + sourcecol + ".")

    #Copy the values. It will overwrite if the column exists
    #or create a new one if it doesn't
    particles[targetcol] = particles[sourcecol]

    return(particles)

"""
--reset_column
"""
def resetcolumn(particles,column,value):

    print("\n>> Replacing all values in " + column + " with " + value + ".")

    particles[column]=value

    return(particles)