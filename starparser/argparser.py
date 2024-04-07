import optparse
import sys
import starparser

def argparse():

    """
    optparse is used to initialize all command-line options.
    """
    
    parser = optparse.OptionParser(usage="Usage: %prog --i starfile [options]",
        version=starparser.__version__)

    #--in_parts, --in_mics, and --in_movies is included for Relion GUI implementation.
    parser.add_option("--i", "--in_parts", "--in_mics", "--in_movies",
        action="store", dest="file", default="", metavar='starfile',
        help="Path to the star file. This is a required input.")

    parser.add_option("--f",
        action="store", dest="parser_file2", default="", metavar='other-starfile',
        help="Path to a second file, if necessary.")

    info_opts = optparse.OptionGroup(
        parser, 'Data Mining Options')

    info_opts.add_option("--extract",
        action="store_true", dest="parser_extractparticles", default=False,
        help="Find particles that match a column header (--c) and query (--q) and write them to a new star file.")

    info_opts.add_option("--limit",
        action="store", dest="parser_limitparticles", type="string", default = "", metavar='column/comparator/value',
        help="Extract particles that match a specific comparison (\"lt\" for less than, \"gt\" for greater than, \"le\" for less than or equal to, \"ge\" for greater than or equal to). The argument to pass is column/comparator/value (e.g. \"DefocusU/lt/40000\" for defocus values less than 40000).")
    
    info_opts.add_option("--count",
        action="store_true", dest="parser_countme", default=False,
        help="Count particles and display the result. Optionally, use --c and --q to count a subset of particles, otherwise counts all.")
    
    info_opts.add_option("--count_mics",
        action="store_true", dest="parser_uniquemics", default=False,
        help="Count the number of unique micrographs. Optionally, use --c and --q to count from a subset of particles, otherwise counts all.")
    
    info_opts.add_option("--list_column",
        action="store", dest="parser_writecol", type="string", default="", metavar='column-name(s)',
        help="Write all values of a column to a file. For example, passing \"MicrographName\" will write all values to MicrographName.txt. To write multiple columns, separate the column names with a slash (for example, \"MicrographName/CoordinateX\" outputs MicrographName.txt and CoordinateX.txt). This can be used with --c and --q to only consider values that match the query, otherwise it lists all values.")

    info_opts.add_option("--find_shared",
        action="store", dest="parser_findshared", type="string", default="", metavar='column-name',
        help="Find particles that are shared between the input star file and the one provided by --f based on the column provided here. Two new star files will be written, one with the shared particles and one with the unique particles.")

    info_opts.add_option("--match_mics",
        action="store_true", dest="parser_matchmics", default=False,
        help="Keep only particles belonging to micrographs that also exist in a second star file (provided by --f).")

    info_opts.add_option("--extract_optics",
        action="store_true", dest="parser_extractoptics", default=False,
        help="Find optics group groups that match a column header (--c) and query (--q) and write the corresponding particles to a new star file.")

    info_opts.add_option("--extract_min",
        action="store", dest="parser_exractmin", type="int", default=-1, metavar='minimum-number',
        help="Find the micrographs that have this minimum number of particles in them and extract all the particles belonging to them.")

    info_opts.add_option("--extract_if_nearby",
        action="store", dest="parser_findnearby", type="float", default=-1, metavar='distance',
        help="Find the nearest particle in a second star file (specified by --f); particles that have a neighbor in the second star file closer than the distance provided here will be written to particles_close.star and those that don't will be written to particles_far.star. Particles that couldn't be matched to a neighbor will be skipped (i.e. if the second star file lacks particles in that micrograph). It will also write a histogram of nearest distances to Particles_distances.png.")

    info_opts.add_option("--extract_clusters",
        action="store", dest="parser_cluster", type="string", default="", metavar='threshold-distance/minimum-per-cluster',
        help="Extract particles that have a minimum number of neighbors within a given radius. For example, passing \"400/4\" extracts particles with at least 4 neighbors within 400 pixels.")

    info_opts.add_option("--extract_indices",
        action="store_true", dest="parser_getindex", default=False,
        help="Extract particles with indices that match a list in a second file (specified by --f). The second file must be a single column list of numbers with values between 1 and the last particle index of the star file.")  

    info_opts.add_option("--extract_random",
        action="store", dest="parser_randomset", type="int", default=-1, metavar='number',
        help="Get a random set of particles totaling the number provided here. Optionally, use --c and --q to extract a random set of each passed query in the specified column. In this case, the output star files will have the names of the query.")

    info_opts.add_option("--remove_poses",
        action="store_true", dest="parser_removeposes", default=False,
        help="Remove poses based on the AngleRot and AngleTilt columns using an interactive plot. Use the lasso tool to select poses to remove.")

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
        help="Sort the column in ascending order and write a new file. Add a slash followed by \"n\" if the column contains numeric values (e.g. \"ClassNumber/n\"); otherwise, it will sort the values as text.")   

    parser.add_option_group(info_opts)

    modify_opts = optparse.OptionGroup(
        parser, 'Modification Options')

    modify_opts.add_option("--operate",
        action="store", dest="parser_operate", type="string", default="", metavar='column[operator]value',
        help="Perform operation on all values of a column. The argument to pass is column[operator]value (without the brackets and without any spaces); operators include \"*\", \"/\", \"+\", and \"-\" (e.g. HelicalTrackLength*0.25). If the terminal throws an error, try surrounding the argument with quotes.")

    modify_opts.add_option("--operate_columns",
        action="store", dest="parser_operatecolumns", type="string", default="", metavar='column[operator]value',
        help="Perform operation between two columns and write to a new column. The argument to pass is column1[operator]column2=newcolumn (without the brackets and without any spaces); operators include \"*\", \"/\", \"+\", and \"-\" (e.g. CoordinateX*OriginX=Shifted). If the terminal throws an error, try surrounding the argument with quotes.")

    modify_opts.add_option("--remove_column",
        action="store", dest="parser_delcolumn", type="string", default="", metavar='column-name(s)',
        help="Remove column, renumber headers, and write to a new star file. E.g. MicrographName. To enter multiple columns, separate them with a slash: MicrographName/CoordinateX.")
    
    modify_opts.add_option("--remove_particles",
        action="store_true", dest="parser_delparticles", default=False,
        help="Remove particles that match a query (specified with --q) within a column header (specified with --c), and write to a new star file.")

    modify_opts.add_option("--remove_duplicates",
        action="store", dest="parser_delduplicates", default="", metavar='column-name',
        help="Remove duplicate particles based on the column provided here (e.g. ImageName).")

    modify_opts.add_option("--remove_mics_list",
        action="store_true", dest="parser_delmics", default=False,
        help="Remove particles that belong to micrographs that have a match in a second file provided by --f (single column list of micrographs).")

    modify_opts.add_option("--keep_mics_list",
        action="store_true", dest="parser_keepmics", default=False,
        help="Keep particles that belong to micrographs that have a match in a second file provided by --f (single column list of micrographs).")

    modify_opts.add_option("--insert_column",
        action="store", dest="parser_insertcol", type="string", default="", metavar='column-name',
        help="Insert a new column that has the values found in the file provided by --f. The file should be a single column and should have an equivalent number to the star file.")     

    modify_opts.add_option("--replace_column",
        action="store", dest="parser_replacecol", type="string", default="", metavar='column-name',
        help="Replace all entries of a column with a list of values found in the file provided by --f. The file should be a single column and should have an equivalent number to the star file.")     

    modify_opts.add_option("--copy_column",
        action="store", dest="parser_copycol", type="string", default="", metavar='source-column/target-column',
        help="Replace all entries of a target column with those of a source column in the same star file. If the target column exists, its values will be replaced. If the target does not exist, a new column will be made. The argument to pass is source-column/target-column (e.g. AngleTiltPrior/AngleTilt)")     

    modify_opts.add_option("--reset_column",
        action="store", dest="parser_resetcol", type="string", default="", metavar='column-name/new-value',
        help="Change all values of a column to the one provided here. The argument to pass is column-name/new-value (e.g. OriginX/0).")

    modify_opts.add_option("--swap_columns",
        action="store", dest="parser_swapcolumns", type="string", default="", metavar='column-name(s)',
        help="Swap columns from another star file (specified with --f). E.g. MicrographName. To enter multiple columns, separate them with a slash: MicrographName/CoordinateX.")

    modify_opts.add_option("--insert_optics_column",
        action="store", dest="parser_insertopticscol", type="string", default="", metavar='column-name/value',
        help="Insert a new column in the optics table with the name and value provided (e.g. AmplitudeContrast/0.1). The value will populate all rows of the optics table.")

    modify_opts.add_option("--fetch_from_nearby",
        action="store", dest="parser_fetchnearby", type="string", default="", metavar='distance/column-name(s)',
        help="Find the nearest particle in a second star file (specified by --f) and if it is within a threshold distance, retrieve its column value to replace the original particle column value. The argument to pass is distance/column-name (e.g. 300/ClassNumber). Particles that couldn't be matched to a neighbor will be skipped (i.e. if the second star file lacks particles in that micrograph). The micrograph paths from MicrographName do not necessarily need to match, just the filenames need to.")

    modify_opts.add_option("--import_mic_values",
        action="store", dest="parser_importmicvalues", type="string", default="", metavar='column-name(s)',
        help="For every particle, find the micrograph that it belongs to in a second star file (provided by --f) and replace the original column value with that of the second star file (e.g. OpticsGroup). The paths do not have to be identical, just the micrograph filename itself. To import multiple columns, separate them with a slash.")

    modify_opts.add_option("--import_particle_values",
        action="store", dest="parser_importpartvalues", type="string", default="", metavar='column-name(s)',
        help="For every particle in the input star file, find the equivalent particle in a second star file (provided by --f) (i.e. those with equivalent ImageName values) and replace the original column value with the one from the second star file. To import multiple columns, separate them with a slash.")

    modify_opts.add_option("--regroup",
        action="store", dest="parser_regroup", type="int", default=0, metavar='particles-per-group',
        help="Regroup particles such that those with similar defocus values are in the same group. Any value can be entered. This is useful if there aren't enough particles in each micrograph to make meaningful groups. Note that Subset selection in Relion can also regroup.")

    modify_opts.add_option("--swap_optics",
        action="store_true", dest="parser_swapoptics", default=False,
        help="Swap the optics table with that of another star file provided by --f.")

    modify_opts.add_option("--new_optics",
        action="store", dest="parser_newoptics", type="string", default="", metavar='opticsgroup-name',
        help="Provide a new optics group name. Use --c and --q to specify which particles belong to this optics group. The optics values from the last entry of the optics table will be duplicated.")

    modify_opts.add_option("--expand_optics",
        action="store", dest="parser_expandoptics", type="string", default="", metavar='opticsgroup-name',
        help="Expand the optics table to its subset optics groups based on a second star file provided by --f. Provide the optics group name to expand. The second star file needs to have the expanded optics table for those micrographs, and a data table with micrograph names and corresponding optics group numbers. The micrograph paths don't have to match exactly between the two files, just the file name.")

    modify_opts.add_option("--relegate",
        action="store_true", dest="parser_relegate", default=False,
        help="Remove optics table and optics column and write to a new star file so that it is compatible with Relion 3.0.")

    parser.add_option_group(modify_opts)
    
    plot_opts = optparse.OptionGroup(
        parser, 'Plotting Options')

    plot_opts.add_option("--histogram",
        action="store", dest="parser_plot", default="", metavar="column-name",
        help="Plot values of a column as a histogram. Optionally, use --c and --q to only plot a subset of particles, otherwise it will plot all. The filename will be that of the column name. Use --t to change the filetype.")

    plot_opts.add_option("--plot_orientations",
        action="store_true", dest="parser_plotangledist", default=False,
        help="Plot the particle orientations based on the AngleRot and AngleTilt columns on a Mollweide projection (longitude and latitude, respectively). Optionally, use --c and --q to only plot a subset of particles, otherwise it will plot all. Use --t to change the filetype.")
    
    plot_opts.add_option("--plot_class_iterations",
        action="store", dest="parser_classiterations", type="string", default="", metavar="classes",
        help="Plot the number of particles per class for all iterations up to the one provided in the input (skips iterations 0 and 1). Pass \"all\" to plot all classes or separate the classes you want with a dash (e.g. 1/2/5). Use --t to change filetype.")
    
    plot_opts.add_option("--plot_class_proportions",
        action="store_true", dest="parser_classproportion", default=False,
        help="Plot the proportion of particles that match different queries in each class. At least two queries (--q, separated by slashes) must be provided along with the column to search in (--c). It will output the proportions and plot the result in Class_proportion.png. Use --t to change filetype.")

    plot_opts.add_option("--plot_coordinates",
        action="store", dest="parser_comparecoords", type="string", default="", metavar="number-of-micrographs",
        help="Plot the particle coordinates for the input star file for each micrograph in a multi-page pdf (red circles). The argument to pass is the total number of micrographs to plot (pass \"all\" to plot all micrographs, but it might take a long time if there are many). Use --f to overlay the coordinates of a second star file (blue circles); in this case, the micrograph names should match between the two star files. The plots are written to Coordinates.pdf.")

    parser.add_option_group(plot_opts)

    query_opts = optparse.OptionGroup(
        parser, 'Query Options')
    
    query_opts.add_option("--c",
        action="store", dest="parser_column", type="string", default="", metavar='column-name(s)',
        help="Column query. E.g. MicrographName. To enter multiple columns, separate them with a slash: MicrographName/CoordinateX.")
    
    query_opts.add_option("--q",
        action="store", dest="parser_query", type="string", default="", metavar='query(ies)',
        help="Particle query term(s) to look for in the values within the specified column. To enter multiple queries, separate them with a slash: 20200101/20200203. To escape a slash, use a \",\". Use --e if the query should exactly match the value.")

    query_opts.add_option("--e",
        action="store_true", dest="parser_exact", default=False, metavar="match-exactly",
        help="Pass this if you want an exact match of the values to the query(ies) provided by --q (e.g. if you want just to look for \"1\" and ignore \"15\".)")
    
    parser.add_option_group(query_opts)

    other_opts = optparse.OptionGroup(
        parser, 'Other Options')

    other_opts.add_option("--opticsless",
        action="store_true", dest="parser_optless", default=False,
        help="Pass this if the file lacks an optics group (more specifically: the star file has exactly one table), such as with Relion 3.0 files.")

    
    other_opts.add_option("--j", help="Ignore this option, multi-threading is not supported yet. The option is included so that Relion can submit starparser jobs.")

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

    """
    The rest of the function parses the input and generates a dictionary for use in decisiontree.py
    """

    #Get the passed arguments from command-line
    options,args = parser.parse_args()

    #If there are less than 4 arguments passed, there were no options passed.
    if len(sys.argv) < 4:
            #parser.print_help()
            #print("\n>> You did not pass the arguments properly. For help, run \"starparser -h\".")
            print("\n>> Usage: starparser --i file.star [options]\n\n>> Help: starparser -h\n")
            sys.exit()

    #Initialize an empty dictionary to place all the parameters in
    params={}

    #Place the passed parameters (or default values if none were passed) into the params dictionary
    for i in options.__dict__.items():
        params[i[0]] = i[1]
        
    #The dictionary is the main input to decisiontree.py
    return(params)