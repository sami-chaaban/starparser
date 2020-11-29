# StarParser

Use this script to manipulate Relion 3.1 star files, including counting, plotting, extracting, and removing data. At the very least, this is a useful alternative to *awk* commands, which can get *awk*ward. See options and examples below.

**Usage:**

```
python starparser.py --i input.star [options]
```

Alternatively, add an alias to your .cshrc (`alias starparser 'python /home/scripts/starparser.py'`) and run the script with:

```
starparser --i input.star [options]
```	

## Getting Started

* You need to have **Python 3** installed and have the **pandas** and **matplotlib** packages. This is probably best done in a new conda environment: `conda create -n star python=3.6 pandas matplotlib`, which is activated with `conda activate star`.

* Your input file needs to be a standard **Relion 3.1** *.star* file with an optics table, followed by another data table (e.g. particle table), followed by a list with tab-delimited columns, (e.g. it does not work on *\*\_model.star* files). Typical files include *run_data.star*, *run_itxxx_data.star*, *movies.star*, etc. Note that the term *particles* here refers to rows in a star file, which may represent objects other than particles, such as movies in a *movies.star* file.

## Options

* **```-h```** : Show a list of  all the options.

### Input

* **```--i```** *```filename```* : Input star file.

* **```--f```** *```filename```* : The name of another file to get information from. Used with ```--swap_columns```, ```--compare```, ```--split_unique```, and ```--replace_column```.

### Plotting

*See below for examples on how to use these options*

* **```--plot_defocus```** : Plot defocus to Defocus_histogram.png based on values in the column \_rlnDefocusU. Can be used with ```-c``` and ```-q``` for a subset, otherwise plots all. The number of bins is calculated using the Freedman-Diaconis rule. Use ```--t``` to change filetype (see the *Output* options).

* **```--plot_classparts```** *```classes```* : Plot the number of particles per class for all iterations up to the one provided in the input. Type "all" to plot all classes, or separate the classes that you want with a slash (e.g. 1/2/5). It can successfully handle filenames that have "\_ct" in them if you've continued from intermediate jobs (only tested on a single continue). Use ```--t``` to change filetype (see the *Output* options).

* **```--class_proportion```** : Find the proportion of particle sets that belong to each class. At least two queries (```-q```, separated by slashes) must be provided along with the column to search in (```-c```). It will output the proportions in percentages and plot the result in Class_proportion.png. Use ```--t``` to change filetype (see the *Output* options).

### Modifying

*See below for examples on how to use these options*

* **```--delete_column```** *```columns```* : Delete column, renumber headers, and output to a new star file (default output.star, or specified with ```--o```). E.g. "*\_rlnMicrographName*". To enter multiple columns, separate them with a slash: "*\_rlnMicrographName/\_rlnCoordinateX*".

* **```--delete_particles```** : Delete particles that match a query (specified with ```-q```) within a column header (specified with ```-c```), and write to a new star file (default output.star, or specified with ```--o```).

* **```--swap_columns```** *```columns```* : Swap columns from another star file (specified with ```--f```). E.g. \_rlnMicrographName. To enter multiple columns, separate them with a slash: "*\_rlnMicrographName/\_rlnCoordinateX*". Note that the columns should be in the same position in both files and the total number of particles should match. The result is written to a new star file (default output.star, or specified with ```--o```).

* **```--regroup```** *```particles-per-group```* : Regroup particles such that those with similar defocus values are in the same group (the number of particles per group is specified here) and write to a new star file (default output.star, or specified with ```--o```). Any value can be entered. This is useful if there aren't enough particles in each micrograph to make meaningful groups. This only works if \_rlnGroupNumber is being used in the star file rater than \_rlnGroupName. Note that Subset selection in Relion should be used for regrouping if possible (which groups on the \*\_model.star intensity scale factors).

* **```--new_optics```** *```optics-group-name```* : Provide a new optics group name. Use ```-c``` and ```-q``` to specify which particles belong to this optics group. The optics values from the last entry of the optics table will be duplicated. The result is written to a new star file (default output.star, or specified with ```--o```).

* **```--replace_column```** *```column-name```* : Replace all entries of the column with those of a file provided by ``--f``. The file should be a single column of values that totals the number of particles in the star file. This is useful when used in conjunction with ```--list_column```, which outputs column values for easy editing before reinsertion with ```--replace_column```. The result is written to a new star file (default output.star, or specified with ```--o```).

* **```--relegate```** : Remove optics table and optics column and write to a new star file (default output.star, or specified with ```--o```) so that it is compatible with Relion 3.0. Note that in some cases this will not be sufficient to be fully compatible with Relion 3.0 and you may have to use ```--delete_column``` to remove other bad columns (e.g. helix-specific columns). If you want to use StarParser on the output file, you will need to then pass ```--opticsless```.

### Data mining

*See below for examples on how to use these options*

* **```--extract_particles```** : Find particles that match a column header (```-c```) and query (```-q```) and write them to a new star file (default output.star, or specified with ```--o```).

* **```--limit_particles```** *```limit```* : Extract particles that match a specific operator ("*lt*" for less than, "*gt*" for greater than). The argument to pass is "column/operator/value" (e.g. "*\_rlnDefocusU/lt/40000*" for defocus values less than 40000).

* **```--count_particles```** : Count particles and print the result. Can be used with ```-c``` and ```-q``` to only count a subset of particles that match the query, otherwise counts all.

* **```--count_mics```** : Count the number of unique micrographs. Can be used with ```-c``` and ```-q``` to only count a subset of particles that match the query, otherwise counts all.

* **```--list_column```** *```columns```* : Write all values of a column to a file (filename will be the name of that column). E.g. \_rlnMicrographName will write to MicrographName.txt. To enter multiple columns, separate them with a slash: \_rlnMicrographName/\_rlnCoordinateX. Can be used with ```-c``` and ```-q``` to only write out values that match the query, otherwise lists all items.

* **```--compare```** *```column```* : Count the number of particles that are shared between the input star file and the one provided by ```--f``` based on the column provided here. Also counts the number that are unique to each star file.

* **```--split_unique```** *```column```* : Split the input star file into two new files: one with particles that are unique to the input file in comparison to the one provided by --f, and one that has particles that are shared between both. Specify the column to use for the comparison here. It will output shared.star and unique.star.

* **```--split_proximal```** *```distance```* : Match particles in the input star file to the closest particle from a second star file provided by ```--f```; those that are closer than the distance provided here will be output to particles_close.star and those that are further will be output to particles_far.star. It will also output a histogram of nearest distances to Particles_distances.png. Use ```--t``` to change filetype (see the *Output* options)

* **```--random```** *```number-of-particles```* : Get a random set of particles totaling the number provided here. Use ```-c``` and ```-q``` to extract a random set of each passed query in the specified column. In this case, the output star files will have the name(s) of the query(ies). Otherwise, a random set from all particles will be output to output.star (or specified with ```--o```).

* **```--split```** *```number-of-splits```* : Split the input star file into the number of star files passed here, making sure not to separate particles that belong to the same micrograph. The files will be called split_#.star. Note that they will not necessarily contain equivalent numbers of particles.

* **```--sortby```** *```column-name```* : Sort the column in ascending order and output a new file to output.star (or specified with ```--o```). By default, it will sort based on the column containing text. Add a slash followed by "*n*" if the column instead contains numeric values (e.g. "*\_rlnClassNumber/n*"). 

### Querying

* **```-c```** *```columns```* : Column query. E.g. "*\_rlnMicrographName*". This is used to look for a specific query specified with ```-q```. To enter multiple columns, separate them with a slash: "*\_rlnMicrographName/\_rlnCoordinateX*". Note the single dash in using this option.

* **```-q```** *```query```* : Particle query term(s) to look for in the values within the specified column. To enter multiple queries, separate them with a slash: 20200101/20200203. Use ```-e``` if the query(ies) should exactly match the values in the column. Note the single dash in using this option.

* **```-e```** : Pass this if you want an exact match of the values to the query(ies) provided by ```-q```. For example, you must pass this if you want just to look for "1" and ignore "15" (which has a "1" in it). Note the single dash in using this option.

### Other

* **```--opticsless```** : Pass this if the file lacks an optics group (more specifically: the star file has exactly one table), such as with Relion 3.0 files. It will create a dummy optics table before moving on. This option does not work with ```--class_proportion``` or commands that require parsing a second file.

### Output

* **```--o```** *```filename```* : Output file name. Default is output.star.

* **```--t```** *```filetype```* : File type of the plot that will be written. Choose between png, jpg, and pdf. Default is png.

---

## Examples

The following examples run the `starparser` command assuming an alias has been created as described above. Otherwise, run it with `python3 starparser.py`.

### Plotting

* Plot a histogram of defocus values.
```
starparser --i run_data.star --plot_defocus
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Output **Defocus_histogram.png**:
![Defocus plot](./Examples/Defocus_histogram.png "Defocus plot")

---

* Plot the number of particles per class for the 25 iterations of a Class3D job.

```
starparser --i run_it025_data.star --plot_classparts all
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Output **Class_distribution.png**:
![Particles per class plot](./Examples/Class_distribution.png "Particles per class plot")

---

* Plot the proportion of particles in each class that belong to particles with the term 200702 versus those with the term 200826 in the \_rlnMicrographName column.

```
starparser --i run_it025_data.star --class_proportion -c _rlnMicrographName -q 200702/200826
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  The percentage in each class will be displayed in terminal.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Output **Class_proportion.png**:
![Class proportion plot](./Examples/Class_proportion.png "Class proportion plot")

---

### Modifying

* **Delete columns**

```
starparser --i run_data.star --o run_data_del.star --delete_column _rlnCtfMaxResolution/_rlnCtfFigureOfMerit 
```
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_del.star** will be identical to run_data.star except will be missing those two columns. The headers in the particles table will be renumbered.

---

* **Delete a subset of particles**

```
starparser --i run_data.star --o run_data_del.star --delete_particles -c _rlnMicrographName -q 200702/200715
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_del.star** will be identical to run_data.star except will be missing any particles that have the term 200702 or 2000715 in the \_rlnMicrographName column. In this case, this was useful to delete particles from specific data-collection days that had the date in the filename.

---

* **Swap columns**

```
starparser --i run_data.star --f run_data_2.star --o run_data_swapped.star --swap_columns _rlnAnglePsi/_rlnAngleRot/_rlnAngleTilt/_rlnNormCorrection/_rlnLogLikeliContribution/_rlnMaxValueProbDistribution/_rlnNrOfSignificantSamples/_rlnOriginXAngst/_rlnOriginYAngst
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_swapped.star** will be output that will be identical to run_data.star except for the columns in the input, which will instead be swapped in from run_data_2.star. This is useful for sourcing alignments from early global refinements.

---

* **Relegate a star file to be compatible with Relion 3.0**

```
starparser --i run_data.star --o run_data_3p0.star --relegate
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_3p0.star** will be output that will be identical to run_data.star except will be missing the optics table and \_rlnOpticsGroup column. The headers in the particles table will be renumbered accordingly.

---

* **Regroup a star file**

```
starparser --i run_data.star --o run_data_regroup200.star --regroup 200
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_regroup200.star** will be output that will be identical to run_data.star except for the \_rlnGroupNumber or \_rlnGroupName columns, which will be renumbered to have 200 particles per group.

---

* **Create a new optics group for a subset of particles**

```
starparser --i run_data.star --o run_data_newoptics.star --new_optics myopticsname -c _rlnMicrographName -q 10090
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_newoptics.star** will be output that will be identical to run_data.star except that a new optics group called *myopticsname* will be created in the optics table and particles with the term 10090 in the \_rlnMicrographName column will have modified \_rlnOpticsGroup and/or \_rlnOpticsName columns to match the new optics group.

---

* **Replace values in a column with those of a text file**

```
starparser --i particles.star --replace_column _rlnOpticsGroup --f newoptics.txt --o particles_newoptics.star
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **particles_newoptics.star** will be output that will be identical to particles.star except for the \_rlnOpticsGroup column, which will have the values found in newoptics.txt.

---

### Data mining

* **Extract a subset of particles**

```
starparser --i run_data.star --o run_data_c1.star --extract_particles -c _rlnClassNumber -q 1 -e
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_c1.star** will be output with only particles that belong to class 1. The `-e` option was passed to avoid extracting any class with the number 1 in it, such as "10", "11", etc.

---

* **Extract particles with limited defoci**

```
starparser --i run_data.star --o run_data_under4um.star --limit_particles _rlnDefocusU/lt/40000
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  A new star file named **run_data_under4um.star** will be output with only particles that have defocus estimations below 4 microns.

---

* **Count specific particles**

```
starparser --i particles.star --o output.star --count_particles -c _rlnMicrographName -q 200702/200715
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  *There are 7726 particles that match ['200702', '200715'] in the specified columns (out of 69120, or 11.2%).*

---

* **Count the number of micrographs**

```
starparser --i run_data.star --count_mics
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  *There are 7994 unique micrographs in this dataset.*

---

* **Count the number of micrographs for specific particles**

```
starparser --i run_data.star --count_mics -c _rlnMicrographName -q 200826
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  *Creating a subset of 2358 particles that match ['200826'] in the columns ['\_rlnMicrographName'] \(or 3.4%\)*

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  *There are 288 unique micrographs in this dataset.*

---

* **List all items from a column in a text file**

```
starparser --i run_data.star --list_column _rlnMicrographName
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  All entries of \_rlnMicrographName will be written to *MicrographName.txt* in a single column.

---

* **List all items from multiple columns in independent text files**

```
starparser --i run_data.star --list_column _rlnDefocusU/_rlnCoordinateX
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  All entries of \_rlnDefocusU will be written to *DefocusU.txt* and all entries of \_rlnCoordinateX will be written to *CoordinateX.txt*.

---

* **List all items from a column that match specific particles**

```
starparser --i run_data.star --list_column _rlnDefocusU -c _rlnMicrographName -q 200826
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Only \_rlnDefocusU entries that have 200826 in \_rlnMicrographName will be written to *DefocusU.txt*.

---

* **Compare particles between star files**

```
starparser --i run_it025_data.star --compare _rlnImageName --f particles.star
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  *run_it025_data.star and particles.star share 36328 particles in the \_rlnImageName column.*

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  *run_it025_data.star has 32792 unique particles and particles.star has 1 unique particles in the \_rlnImageName column.*

---

* **Extract particles that are unique and shared between two star files**

```
starparser --i run_data1.star --split_unique _rlnMicrographName --f run_data2.star
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Two new star files will be created named shared.star and unique.star that will have only the particles that are unique to run_data1.star relative to run_data2star (unique.star) and only the particles that are shared between them (shared.star) based on the \_rlnMicrographName column.

---

* **Extract a random set of specific particles**

```
starparser --i run_it025_data.star --random 10000 particles.star -c _rlnMicrographName -q DOA3/OAA2
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Two new star files will be created named DOA3_10000.star and OAA2_10000.star that will have a random set of 10000 particles that match DOA3 and OAA2 in the \_rlnMicrographName column, repsectively.

---

* **Split a star file**

```
starparser --i particles.star --split 3
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&#8594;  Three new star files called split_1.star, split_2.star, and split_3.star will be created with roughly equal numbers of particles. In this case, particles.star has 69120 particles and the split star files have 23053, 23042, and 23025 particles, respectively.

---

## Version

* **1.7** - November 2020

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
