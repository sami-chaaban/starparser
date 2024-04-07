# starparser

Use this package to manipulate Relion star files, including counting, modifying, plotting, and sifting the data. At the very least, this is a useful alternative to *awk* commands, which can get *awk*ward. Below is a description of the command-line options with some examples. Alternatively, use starparser within Relion or load the modules in your own Python scripts.

Some of the options below are already available in Relion with "relion_star_handler".

1. [Installation](#installation)
2. [Command-line options](#cmdops)
3. [Tips](#tips)
4. [Limitations](#limits)
5. [Relion GUI usage](#reliongui)
6. [Scripting](#scripts)
7. [Examples](#examples)
8. [License](#license)

## Installation<a name="installation"></a>

* Set up a fresh conda environment with Python >= 3.8: `conda create -n sp python=3.8`

* Activate the environment: `conda activate sp`.

* Install starparser: **`pip install starparser`**

## Command-line options<a name="cmdops"></a>

### Usage

```
starparser [input] [options]
```

Typically, you just need to pass the star file ```starparser --i input.star``` followed by the desired option and its arguments.

```
starparser --i particles.star --count
```

```
starparser --i particles.star --list_column OriginX
```

For some options, a second star file can also be passed as input ```--f secondfile.star```.

```
starparser --i particles1.star --find_shared MicrographName --f particles2.star
```

The list of options are organized by [Data Mining](#mining), [Modifications](#modify), and [Plots](#plot). Arguments that are not required are surrounded by parentheses in the descriptions below. Do not include the parentheses in your arguments.

### Input

**```--i```** *```filename.star```*

Path to the star file. This is a required input.

**```--f```** *```filename.star```*

Path to a second file, if necessary.

### Data Mining Options<a name="mining"></a>

**```--extract```** *`--c column --q query (--e)`*

Find particles that match a column header ```--c``` and query ```--q``` (see the [*Querying*](#query) options) and write them to a new star file (default output.star, or specified with ```--o```).

**```--limit```** *```column/comparator/value```*

Extract particles that match a specific comparison (*lt* for less than, *gt* for greater than, *le* for less than or equal to, *ge* for greater than or equal to). The argument to pass is "column/comparator/value" (e.g. *DefocusU/lt/40000* for defocus values less than 40000).

**```--count```** *`(--c column --q query (--e))`*

Count the number of particles and display the result. Optionally, this can be used with ```--c``` and ```--q``` to only count a subset of particles that match the query (see the [*Querying*](#query) options), otherwise counts all.

**```--count_mics```** *`(--c column --q query (--e))`*

Count the number of unique micrographs and display the result. Optionally, this can be used with ```--c``` and ```--q``` to only count a subset of particles that match the query (see the [*Querying*](#query) options), otherwise counts all.

**```--list_column```** *```column-name(s)```* *`(--c column --q query (--e))`*

Write all values of a column to a file. For example, passing *MicrographName* will write all values to MicrographName.txt. To output multiple columns, separate the column names with a slash (for example, *MicrographName/CoordinateX* outputs MicrographName.txt and CoordinateX.txt). Optionally, this can be used with ```--c``` and ```--q``` to only consider particles that match the query (see the [*Querying*](#query) options), otherwise it lists all values.

**```--find_shared```** *```column-name```* *`--f otherfile.star`*

Find particles that are shared between the input star file and the one provided by ```--f``` based on the column provided here. Two new star files will be output, one with the shared particles and one with the unique particles.

**```--match_mics```**

Keep only particles from micrographs that also exist in a second star file provided by ```--f```. Output will be written to output.star (or specified with ```--o```).

**```--extract_optics```**

Find optics groups that match a column header ```--c``` and query ```--q``` (see the [*Querying*](#query) options) and write the corresponding particles to a new star file. Output will be written to output.star (or specified with ```--o```).

**```--extract_min```** *```minimum-value```*

Find the micrographs that have this minimum number of particles in them and extract all the particles belonging to them.

**```--extract_if_nearby```** *```distance```* *`--f otherfile.star`*

For every particle in the input star file, check the nearest particle in a second star file provided by ```--f```; particles that have a neighbor closer than the distance (in pixels) provided here will be written to particles_close.star, and those that don't will be written to particles_far.star. Particles that couldn't be matched to a neighbor will be skipped (i.e. if the second star file lacks particles in that micrograph). It will also output a histogram of nearest distances to Particles_distances.png (use ```--t``` to change the file type; see the [*Output*](#output) options).

**```--extract_clusters```** *```threshold-distance/minimum-number```*

Extract particles that have a minimum number of neighbors within a given radius. For example, passing *400/4* extracts particles with at least 4 neighbors within 400 pixels.

**```--extract_indices```** *`--f indices.txt`*

Extract particles with indices that match a list in a second file (specified by ```--f```). The second file must be a single column list of numbers with values between 1 and the last particle index of the star file. The result is written to output.star (or specified with ```--o```).

**```--extract_random```** *```number-of-particles```* *`(--c column --q query (--e))`*

Get a random set of particles totaling the number provided here. Optionally, use ```--c``` and ```--q``` to extract a random set of each passed query in the specified column (see the [*Querying*](#query) options); in this case, the output star files will have the name(s) of the query(ies). Otherwise, a random set from all particles will be written to output.star (or specified with ```--o```).

**```--remove_poses```**

Remove poses based on the AngleRot and AngleTilt columns using an interactive scatter plot. Use the lasso tool to select poses to remove then press enter to remove them. Continue removing and then press "e" to save and exit. Output will be written to output.star (or specified with ```--o```).

**```--split```** *```number-of-files```*

Split the input star file into the number of star files passed here, making sure not to separate particles that belong to the same micrograph. The files will have the input file name with the suffix "\_split-#". Note that they will not necessarily contain exactly the same number of particles.

**```--split_classes```**

Split the input star file into independent star files for each class. The files will have the names "Class_#.star". 

**```--split_optics```**

Split the input star file into independent star files for each optics group. The files will have the names of the optics group.

**```--sort_by```** *```column-name(/n)```*

Sort the columns in ascending order according to the column passed here. Outputs a new file to output.star (or specified with ```--o```). Add a slash followed by "*n*" if the column contains numeric values (e.g. *ClassNumber/n*); otherwise, it will sort the values as text. 

### Modification Options<a name="modify"></a>

**```--operate```** *```column-name[operator]value```*

Perform operation on all values of a column. The argument to pass is column[operator]value (without the brackets and without any spaces); operators include "\*", "/", "+", and "-" (e.g. *HelicalTrackLength\*0.25*). The result is written to a new star file (default output.star, or specified with ```--o```). If your terminal throws an error, try surrounding the argument with quotations (e.g. *"HelicalTrackLength\*0.25"*).

**```--operate_columns```** *```column1[operator]column2=newcolumn```*

Perform operation between two columns and write to a new column. The argument to pass is column1[operator]column2=newcolumn (without the brackets and without any spaces); operators include "\*", "/", "+", and "-" (e.g. *CoordinateX+OriginX=ShiftedX*). If your terminal throws an error, try surrounding the argument with quotations (e.g. *"CoordinateX+OriginX=ShiftedX"*).

**```--remove_column```** *```column-name(s)```*

Remove column, renumber headers, and write to a new star file (default output.star, or specified with ```--o```). E.g. *MicrographName*. To enter multiple columns, separate them with a slash: *MicrographName/CoordinateX*. Note that "relion_star_handler --remove_column" also does this.

**```--remove_particles```** *`--c column --q query (--e)`*

Remove particles that match a query (specified with ```--q```) within a column header (specified with ```--c```; see the [*Querying*](#query) options), and write to a new star file (default output.star, or specified with ```--o```).

**```--remove_duplicates```** *```column-name```*

Remove duplicate particles based on the column provided here (e.g. *ImageName*) (one instance of the duplicate is retained).

**```--remove_mics_list```** *`--f micrographs.txt`*

Remove particles that belong to micrographs that have a match in a second file provided by ```--f```, and write to a new star file (default output.star, or specified with ```--o```). You only need to have the micrograph names and not necessarily the full paths in the second file.

**```--keep_mics_list```** *`--f micrographs.txt`*

Keep particles that belong to micrographs that have a match in a second file provided by ```--f```, and write to a new star file (default output.star, or specified with ```--o```). You only need to have the micrograph names and not necessarily the full paths in the second file.

**```--insert_column```** *```column-name```* *`--f values.txt`*

Insert a new column that doesn't already exist with the values found in the file provided by ```--f```. The file should be a single column and should have an equivalent number to the star file. The result is written to a new star file (default output.star, or specified with ```--o```).

**```--replace_column```** *```column-name```* *`--f values.txt`*

Replace all entries of a column with a list of values found in the file provided by ```--f```. The file should be a single column and should have an equivalent number to the star file. This is useful when used in conjunction with ```--list_column```, which outputs column values for easy editing before reinsertion with ```--replace_column```. The result is written to a new star file (default output.star, or specified with ```--o```).

**```--copy_column```** *```source-column/target-column```*

Replace all entries of a target column with those of a source column in the same star file. If the target column does not exist, a new column will be made. The argument to pass is source-column/target-column (e.g. *AngleTiltPrior/AngleTilt*). The result is written to a new star file (default output.star, or specified with ```--o```)

**```--reset_column```** *```column-name/new-value```*

Change all values of a column to the one provided here. The argument to pass is column-name/new-value (e.g. *OriginX/0*). The result is written to a new star file (default output.star, or specified with ```--o```)

**```--swap_columns```** *```column-name(s)```* *`--f otherfile.star`*

Swap columns from another star file (specified with ```--f```). For example, pass *MicrographName* to swap that column. To enter multiple columns, separate them with a slash: *MicrographName/CoordinateX*. Note that the total number of particles should match. The result is written to a new star file (default output.star, or specified with ```--o```).

**```--insert_optics_column```** *```column-name/value```*

Insert a new column in the optics table with the name and value provided (e.g. *AmplitudeContrast/0.1*). The value will populate all rows of the optics table. The result is written to a new star file (default output.star, or specified with ```--o```).

**```--fetch_from_nearby```** *```distance/column-name(s)```* *`--f otherfile.star`*

Find the nearest particle in a second star file (specified with ```--f```) and if it is within a threshold distance, retrieve its column value to replace the original particle column value. The argument to pass is distance/column-name(s) (e.g. *300/ClassNumber* or *100/AnglePsi/HelicalTubeID*). Outputs to output.star (or specified with ```--o```). Particles that couldn't be matched to a neighbor will be skipped (i.e. if the second star file lacks particles in that micrograph). The micrograph paths from MicrographName do not necessarily need to match, just the filenames need to.

**```--import_mic_values```** *```column-name(s)```* *`--f otherfile.star`*

For every particle, find the micrograph that it belongs to in a second star file (specified with ```--f```) and replace the original column value with that of the second star file (e.g. *OpticsGroup*). The paths do not have to be identical, just the micrograph filename itself. To import multiple columns, separate them with a slash. The result is written to a new star file (default output.star, or specified with ```--o```).

**```--import_particle_values```** *```column-name(s)```* *`--f otherfile.star`*

For every particle in the input star file, find the equivalent particle in a second star file (specified with ```--f```) (i.e. those with identical *ImageName* values) and replace the original column value with the one from the second star file. To import multiple columns, separate them with a slash.

**```--regroup```** *```particles-per-group```*

Regroup particles such that those with similar defocus values are in the same group (the number of particles per group is specified here) and write to a new star file (default output.star, or specified with ```--o```). Any value can be entered. This is useful if there aren't enough particles in each micrograph to make meaningful groups. This only works if *GroupNumber* is being used in the star file rater than *GroupName*. Note that Subset selection in Relion should be used for regrouping if possible (which groups on the \*\_model.star intensity scale factors).

**```--swap_optics```**

Swap the optics table with that of another star file provided by ```--f```. The result is written to a new star file (default output.star, or specified with ```--o```).

**```--new_optics```** *```opticsgroup-name```* *`--c column --q query (--e)`*

Provide a new optics group name. Use ```--c``` and ```--q``` to specify which particles belong to this optics group (see the [*Querying*](#query) options). The optics values from the last entry of the optics table will be duplicated. The result is written to a new star file (default output.star, or specified with ```--o```).

**```--expand_optics```** *```opticsgroup-name```* *`--f filewithoptics.star`*

Expand the optics table to its subset optics groups based on a second star file provided by ```--f```. Provide the optics group name to expand. The second star file needs to have the expanded optics table for those micrographs, and a data table with micrograph names and corresponding optics group numbers. The micrograph paths don't have to match exactly between the two files, just the file name. The result is written to a new star file (default output.star, or specified with ```--o```).

**```--relegate```**

Remove optics table and optics column and write to a new star file (default output.star, or specified with ```--o```) so that it is compatible with Relion 3.0. Note that in some cases this will not be sufficient to be fully compatible with Relion 3.0 and you may have to use ```--remove_column``` to remove other bad columns (e.g. helix-specific columns). Note that to use starparser on Relion 3.0 star files, you need to pass the ```--opticsless``` option.

### Plotting Options<a name="plot"></a>

**```--histogram```** *```column-name```* *`(--c column --q query (--e))`*

Plot values of a column as a histogram. Optionally, use ```--c``` and ```--q``` to only plot a subset of particles (see the [*Querying*](#query) options), otherwise it will plot all. The filename will be that of the column name. Use ```--t``` to change the file type (see the [*Output*](#output) options). The number of bins is calculated using the Freedman-Diaconis rule. Note that "relion_star_handler --hist_column" also does this.

**```--plot_orientations```** *`(--c column --q query (--e))`*

Plot the particle orientations based on the *AngleRot* and *AngleTilt* columns on a Mollweide projection (longitude and latitude, respectively). Optionally, use ```--c``` and ```--q``` to only plot a subset of particles, otherwise it will plot all. The result will be saved to Particle_orientations.png. Use ```--t``` to change the file type (see the [*Output*](#output) options).

**```--plot_class_iterations```** *```classes```*

Plot the number of particles per class for all iterations up to the one provided in the input (skips iterations 0 and 1). Pass "all" to plot all classes, or separate the classes that you want with a slash (e.g. *1/2/5*). It can successfully handle filenames that have "\_ct" in them if you've continued from intermediate jobs (only tested on a single continue). Use ```--t``` to change the file type (see the [*Output*](#output) options).

**```--plot_class_proportions```** *`--c column --q queries (--e)`*

Find the proportion of particle sets that belong to each class. Pass at least two queries (```--q```, queries are separated by a slash from each other) along with the column ```--c``` to search in (see the [*Querying*](#query) options). It will display the proportions in percentages and plot the result to Class_proportion.png. Use ```--t``` to change the file type (see the [*Output*](#output) options).

**```--plot_coordinates```** *```number-of-micrographs(/circle-size)```*

 Plot the particle coordinates for the input star file for each micrograph in a multi-page pdf (red circles). The argument to pass is the total number of micrographs to plot (pass \"all\" to plot all micrographs, but it might take a long time if there are many). Make sure you are running it in the Relion directory so that the micrograph .mrc files can be properly sourced (or change the *MicrographName* column to absolute paths). Use ```--f``` to overlay the coordinates of a second star file (larger blue circles); in this case, the micrograph names should match between the two star files. Optionally, pass the desired size of the circle after a slash (e.g. *1/250* for 1 micrograph and a circle size of 250 pixels). The plots are written to Coordinates.pdf.

### Querying<a name="query"></a>

**```--c```** *```column-name(s)```*

Column query term(s). E.g. *MicrographName*. This is used to look for a specific query specified with ```--q```. In cases where you can enter multiple columns, separate them with a slash: *MicrographName/CoordinateX*.

**```--q```** *```query(ies)```*

Particle query term(s) to look for in the values within the specified column. To enter multiple queries, separate them with a slash (e.g. 20200101/20200203 to request matching either of the two queries). To escape a slash, precede it with "," (i.e. ,/). Use ```--e``` if the query(ies) should exactly match the values in the column (see below).

**```--e```**

Pass this if you want an exact match of the values to the query(ies) provided by ```--q```. For example, you must pass this if you want just to look for "1" and ignore "15" (which has a "1" in it).

### Other

**```--opticsless```**

Pass this if the input star file lacks an optics group (more specifically: the star file has exactly one table), such as with Relion 3.0 files. It will create a dummy optics table before moving on. This option does not work with ```--plot_class_proportions``` or commands that require parsing a second file.

### Output<a name="output"></a>

**```--o```** *```filename```*

Output file name. Default is output.star.

**```--t```** *```filetype```*

File type of the plot that will be written. Choose between png, jpg, svg, and pdf. The default is png.

---

## Tips<a name="tips"></a>

* Your input file needs to be a standard **Relion** *.star* file. Typical files include *particles.star*, *run_data.star*, *run_itxxx_data.star*, *movies.star*, *micrographs_ctf.star*, etc. You cannot parse *\*\_model.star* files for example.

* The term *particles* here refers to rows in a star file, but the star files don't need to contain particles (e.g. parsing movies in a *movies.star* file).

* Columns can be specified by their full or short names (e.g. \_rlnColumnName, rlnColumnName, or ColumnName). If scripting with the starparser package, columns are specified as their full name (i.e. \_rlnColumnName).

* If the star file lacks an optics table, such as those from Relion 3.0, add the ```--opticsless``` option to parse it.

---

## Limitations<a name="limits"></a>

* ```--opticsless``` does not work when the second star file (```--f```) lacks an optics table or when multiple star files are being read. There is little incentive to fix this since few still use Relion 3.0.

* Data mining options do not check if the subset that was created has rendered one of the optics groups void; they retain all optics groups. Optics groups should be modified manually.

* ```--split_optics``` does not renumber the optics groups that were greater than 1 back to 1, although this does not affect any behavior downstream in Relion and elsewhere.

* The ```--plot_coordinates``` circle size does not exactly match the requested value. If you need it to be exact, save the file as pdf with ```--t pdf``` and open the plot in illustrator to modify the circle size.

* The Freedman-Diaconis rule for histogram binning is not always appropriate.

---

## Relion GUI Usage<a name="reliongui"></a>

* Use the External commands tab to run starparser within Relion. You don't need the double dash ```--``` for the options (i.e. "Param label").

![Relion-GUI-1](https://github.com/sami-chaaban/StarParser/blob/main/Images/Relion-1.png?raw=true "Relion-GUI-1")

![Relion-GUI-2](https://github.com/sami-chaaban/StarParser/blob/main/Images/Relion-2.png?raw=true "Relion-GUI-2")

![Relion-GUI-3](https://github.com/sami-chaaban/StarParser/blob/main/Images/Relion-3.png?raw=true "Relion-GUI-3")

---

## Scripting<a name="scripts"></a>

* To parse a star file for downstream use in a Python script:

```python
from starparser import fileparser
particles, metadata = fileparser.getparticles("file.star")
```

* The particles DataFrame can be manipulated with pandas functions (see the example below). However, some starparser options are available:

```python
from starparser import columnplay

#Remove columns with delcolumn(particles, [columns], metadata)
new_particles, new_metadata = columnplay.delcolumn(particles, ["_rlnMicrographName", "_rlnOpticsGroup"], metadata)

#Operate on a column with operate(particles, column, operator, value) where operator is one of "multiply", "divide", "add", or "subtract"
operated_particles = columnplay.operate(particles, "_rlnHelicalTrackLength", "multiply", 0.25)

from starparser import particleplay

#Remove particles with delparticles(particles, [columns], [queries], queryexact)
new_particles = particleplay.delparticles(particles, ["_rlnMicrographName"], ["0207"], False)

#Remove duplicates with delduplicates(particles, column)
noduplicate_particles = particleplay.delduplicates(particles, "_rlnImageName")

#Limit values with limit(particles, column, limit, operator)
limit_particles = particleplay.limitparticles(particles, "_rlnDefocusU", 30000, "lt")

from starparser import specialparticles

#Keep particles that have a nearest neighbor in another star file within a threshold with findnearby(particles, otherparticles, threshold)
otherparticles, metadata2 = fileparser.getparticles("dataset2/particles.star")
far_particles, close_particles, distances = specialparticles.findnearby(particles, otherparticles, 600)

#Extract particles that have a minimum number of neighbors within a radius with getcluster(particles, threshold, minimum)
clusterparticles = specialparticles.getcluster(particles, 250, 4)
``` 

* After manipulating the particles, you can write out a new star file:

```python
fileparser.writestar(new_particles, metadata, "processed-particles.star")
```

* Here is a simple workflow to iterate through particles, one micrograph at a time

```python
from starparser import fileparser

#import data to a pandas dataframe
particles, metadata = fileparser.getparticles("particles.star")

#group by micrographs
micrographs = particles.groupby(["_rlnMicrographName"])

keeplist = []

#iterate through the micrographs
for idm, micrograph in micrographs:

    #iterate through the particles in the current micrograph
    for idp, particle in micrograph.iterrows():

        #access specific values with particle["_rlnColumnName"]

        ...
```

* Here is a practical example showing how to keep only one of three particles of a helix

```python
from starparser import fileparser

#import data to a pandas dataframe
particles, metadata = fileparser.getparticles("particles.star")

#group by micrographs
micrographs = particles.groupby(["_rlnMicrographName"])

keeplist = []

#iterate through the micrographs
for idm, micrograph in micrographs:
    
    #get the helices for the current micrograph
    helices = micrograph.groupby(["_rlnHelicalTubeID"])

    #iterate through the helices for this micrograph
    for idh, helix in helices:
        
        #get the indices for the particles of the current helix and turn it into a list
        indices = helix.index.tolist()
        
        #get the indices for one of every three particles of that helix and store it in keeplist
        keeplist.append(indices[::3])
    
#flatten the aggregate list; this is now the list of particle indices to keep
keeplist = [item for sublist in keeplist for item in sublist]
    
#write out a star file only containing those particles to keep
fileparser.writestar(particles[particles.index.isin(keeplist)], metadata, "particles_purged.star")
```

---

## Examples<a name="examples"></a>

### Plotting

* Plot a histogram of defocus values.
```
starparser --i run_data.star --histogram DefocusU
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Output figure to **DefocusU.png**:
![Defocus plot](https://github.com/sami-chaaban/StarParser/blob/main/Images/Defocus_histogram.png?raw=true "Defocus plot")

---

* Plot the particle orientation distribution.
```
starparser --i run_data.star --plot_orientations
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Output figure to **Particle_orientations.png**:
![Orientation plot](https://github.com/sami-chaaban/StarParser/blob/main/Images/Particle_orientations.png?raw=true "Particle orientations")

---

* Plot the number of particles per class for the 25 iterations of a Class3D job.

```
starparser --i run_it025_data.star --plot_class_iterations all
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Output figure to **Class_distribution.png**:
![Particles per class plot](https://github.com/sami-chaaban/StarParser/blob/main/Images/Class_distribution.png?raw=true "Particles per class plot")

---

* Plot the proportion of particles in each class that belong to particles with the term 200702 versus those with the term 200826 in the MicrographName column.

```
starparser --i run_it025_data.star --plot_class_proportions --c MicrographName --q 200702/200826
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  The percentage in each class will be displayed in terminal.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Output figure to **Class_proportion.png**:
![Class proportion plot](https://github.com/sami-chaaban/StarParser/blob/main/Images/Class_proportion.png?raw=true "Class proportion plot")

---

* Overlay the coordinates of two star files for 1 micrograph with a marker size of 200 pixels.

```
starparser --i particles.star --f select_particles.star --plot_coordinates 1/200
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Plotting coordinates from the star file (red circles) and second file (blue circles) for 1 micrograph(s).

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Output figure to **Coordinates.pdf**:

![Coordinates plot](https://github.com/sami-chaaban/StarParser/blob/main/Images/Coordinates.png?raw=true "Coordinates plot")

---

### Modifying

**Remove columns**

```
starparser --i run_data.star --o run_data_del.star --remove_column CtfMaxResolution/CtfFigureOfMerit 
```
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_del.star** will be identical to run_data.star except will be missing those two columns. The headers in the particles table will be renumbered.

---

**Remove a subset of particles**

```
starparser --i run_data.star --o run_data_del.star --remove_particles --c MicrographName --q 200702/200715
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_del.star** will be identical to run_data.star except will be missing any particles that have the term 200702 or 2000715 in the MicrographName column. In this case, this was useful to remove particles from specific data-collection days that had the date in the filename.

---

**Replace values in a column with those of a text file**

```
starparser --i particles.star --replace_column OpticsGroup --f newoptics.txt --o particles_newoptics.star
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **particles_newoptics.star** will be output that will be identical to particles.star except for the OpticsGroup column, which will have the values found in newoptics.txt.

---

**Swap columns**

```
starparser --i run_data.star --f run_data_2.star --o run_data_swapped.star --swap_columns AnglePsi/AngleRot/AngleTilt/NormCorrection/LogLikeliContribution/MaxValueProbDistribution/NrOfSignificantSamples/OriginXAngst/OriginYAngst
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_swapped.star** will be output that will be identical to run_data.star except for the columns in the input, which will instead be swapped in from run_data_2.star. This is useful for sourcing alignments from early global refinements.

---

**Regroup a star file**

```
starparser --i run_data.star --o run_data_regroup200.star --regroup 200
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_regroup200.star** will be output that will be identical to run_data.star except for the GroupNumber or GroupName columns, which will be renumbered to have 200 particles per group.

---

**Create a new optics group for a subset of particles**

```
starparser --i run_data.star --o run_data_newoptics.star --new_optics myopticsname --c MicrographName --q 10090
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_newoptics.star** will be output that will be identical to run_data.star except that a new optics group called *myopticsname* will be created in the optics table and particles with the term 10090 in the MicrographName column will have modified OpticsGroup and/or OpticsName columns to match the new optics group.

---

**Relegate a star file to be compatible with Relion 3.0**

```
starparser --i run_data.star --o run_data_3p0.star --relegate
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_3p0.star** will be output that will be identical to run_data.star except will be missing the optics table and OpticsGroup column. The headers in the particles table will be renumbered accordingly.

---

### Data mining

**Extract a subset of particles**

```
starparser --i run_data.star --o run_data_c1.star --extract --c ClassNumber --q 1 --e
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_c1.star** will be output with only particles that belong to class 1. The `--e` option was passed to avoid extracting any class with the number 1 in it, such as "10", "11", etc.

---

**Extract particles with limited defoci**

```
starparser --i run_data.star --o run_data_under4um.star --limit DefocusU/lt/40000
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_under4um.star** will be output with only particles that have defocus estimations below 4 microns.

---

* **Remove specific poses from a star file**

```
starparser --i particles.star --o particles_remove_weird_poses.star --remove_poses
```

![Remove Poses](https://github.com/sami-chaaban/StarParser/blob/main/Images/Remove_poses.gif?raw=true "Remove Poses")

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  *Removed 2544 particles out of 19519.*

---

**Count specific particles**

```
starparser --i particles.star --o output.star --count --c MicrographName --q 200702/200715
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  *There are 7726 particles that match ['200702', '200715'] in the specified columns (out of 69120, or 11.2%).*

---

**Count the number of micrographs**

```
starparser --i run_data.star --count_mics
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  *There are 7994 unique micrographs in this dataset.*

---

**Count the number of micrographs for specific particles**

```
starparser --i run_data.star --count_mics --c MicrographName --q 200826
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  *Creating a subset of 2358 particles that match ['200826'] in the columns ['\_rlnMicrographName'] \(or 3.4%\)*

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  *There are 288 unique micrographs in this dataset.*

---

**List all items from a column in a text file**

```
starparser --i run_data.star --list_column MicrographName
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  All entries of MicrographName will be written to *MicrographName.txt* in a single column.

---

**List all items from multiple columns in independent text files**

```
starparser --i run_data.star --list_column DefocusU/CoordinateX
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  All entries of DefocusU will be written to *DefocusU.txt* and all entries of CoordinateX will be written to *CoordinateX.txt*.

---

**List all items from a column that match specific particles**

```
starparser --i run_data.star --list_column DefocusU --c MicrographName --q 200826
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Only DefocusU entries that have 200826 in MicrographName will be written to *DefocusU.txt*.

---

**Compare particles between star files and extract those that are shared and unique**

```
starparser --i run_data1.star --find_shared MicrographName --f run_data2.star
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Two new star files will be created named shared.star and unique.star that will have only the particles that are unique to run_data1.star relative to run_data2.star (unique.star) and only the particles that are shared between them (shared.star) based on the MicrographName column.

---

**Extract particles that have a nearest neighbor in a second star file closer than a threshold distance**

```
starparser --i particles1.star --f particles2.star --extract_if_nearby 650
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Two new star files will be created named particles_close.star and particles_far.star that will have particles that have a nearest neighbor closer than 650 pixels or not, respectively.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Output figure to **Particle_distances.png**:
![Particle distances](https://github.com/sami-chaaban/StarParser/blob/main/Images/Particle_distances.png?raw=true "Particle distances")

---

**Extract a random set of specific particles**

```
starparser --i run_it025_data.star --extract_random 10000 --c MicrographName --q DOA3/OAA2
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Two new star files will be created named DOA3_10000.star and OAA2_10000.star that will have a random set of 10000 particles that match DOA3 and OAA2 in the MicrographName column, respectively.

---

**Split a star file**

```
starparser --i particles.star --split 3
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Three new star files called split_1.star, split_2.star, and split_3.star will be created with roughly equal numbers of particles. In this example, particles.star has 69120 particles and the split star files have 23053, 23042, and 23025 particles, respectively.

---

## License<a name="license"></a>

This project is licensed under the MIT License - see the [LICENSE.txt](https://github.com/sami-chaaban/StarParser/blob/main/LICENSE.txt) file for details.
