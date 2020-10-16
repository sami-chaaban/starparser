# StarParser

Use this script to manipulate Relion 3.1 star files. See options and examples below.

Usage:

```
python3 starparser.py --i input.star [options]
```

Alternatively, add an alias to your .cshrc (`alias starparser 'python3 /home/scripts/starparser.py'`) and run the script with `starparser --i input.star [options]`	

## Getting Started

* You need to have **Python 3** installed and have the **pandas** package. This is probably best done in a new conda environment: `conda create -n star python=3.6 pandas`, which is activated with `conda activate star`.

* Your star file needs to be a standard **Relion 3.1** star file with an optics table, particle table, and particle list with tab delimited columns, (e.g. it does not work on \*\_model.star files).

## Options

* ```--plot_defocus``` Plot defocus to Defocus_histogram.png. Can be used with -c and -q for a subset, otherwise plots all.

* ```--delete_column``` Delete column and renumber headers. E.g. \_rlnMicrographName. To enter multiple columns, separate them with a slash: \_rlnMicrographName/\_rlnCoordinateX.

* ```--delete_particles``` Delete particles. Pick a column header (-c) and query (-q) to delete particles that match it.

* ```--extract_particles``` Write a star file with particles that match a column header (-c) and query (-q).

* ```--count_particles``` Count particles and print the result. Can be used with -c and -q for a subset count, otherwise counts all.

* ```--count_mics``` Count the number of unique micrographs. Can be used with -c and -q for a subset count, otherwise counts all.

* ```--max_defocus``` Extract particles with defocus values less than this value (Angstroms). Can be used with -c and -q to only consider a subset.

* ```--list_column``` Write all values of a column to a file (filename is the header). E.g. \_rlnMicrographName. To enter multiple columns, separate them with a slash: \_rlnMicrographName/\_rlnCoordinateX. Can be used with -c and -q for a subset count, otherwise lists all items.

* ```--swap_columns``` Swap columns from another star file (specified with --f). E.g. \_rlnMicrographName. To enter multiple columns, separate them with a slash: \_rlnMicrographName/\_rlnCoordinateX. Note that they should be in the same position in both files.

* ```--relegate``` Remove optics table and optics column. This may not be sufficient to be fully compatible with Relion 3.0. Use --delete_column to remove other bad columns before this, if necessary.

* ```--regroup``` Regroup particles such that those with similar defocus values are in the same group. Any value can be entered. This is useful if there aren't enough particles in each micrograph to make meaningful groups. Note that Subset selection in Relion should be used for regrouping if possible.

* ```--o``` Output file name. Default is output.star.

* ```--f``` Name of second file to extract columns from.

* ```-c``` Column query. E.g. \_rlnMicrographName. This is used to look for a specific query specified with -q. To enter multiple columns, separate them with a slash: \_rlnMicrographName/\_rlnCoordinateX. Note the single dash.

* ```-q``` Query term to look for in the column specified by -c. To enter multiple queries, separate them with a slash: 20200101/20200203. Note the single dash.

## Examples

The following examples run the starparser command assuming an alias has been created as described above, otherwise, run it with `python3 starparser.py`.

---

* Plot a histogram of defocus values.

```
starparser --i run_data.star --plot_defocus
```

---

* Plot a histogram of defocus values from a subset of micrographs that contain "200826" or "200827".

```
starparser --i run_data.star --plot_defocus -c _rlnMicrographName -q 200826/200827
```

---

* Delete the \_rlnCtfMaxResolution and \_rlnCtfFigureOfMerit columns.

```
starparser --i run_data.star --o output.star --delete_column _rlnCtfMaxResolution/_rlnCtfFigureOfMerit 
```

---

* Delete all particles with "200702" or "200715" in the \_rlnMicrographName column.

```
starparser --i run_data.star --o output.star --delete_particles -c _rlnMicrographName -q 200702/200715
```

---

* Make a new star file with only particles that have "1" in the \_rlnClassNumber column.

```
starparser --i run_data.star --o output.star --extract_particles -c _rlnClassNumber -q 1
```

---

* Count the number of particles with "200702" or "200715" in the \_rlnMicrographName column.

```
starparser --i run_data.star --o output.star --count_particles -c _rlnMicrographName -q 200702/200715
```

---

* Count the total number of unique micrographs.

```
starparser --i run_data.star --count_mics
```

---

* Count the total number of unique micrographs in the subset that contain "200826" in the \_rlnMicrographName column.

```
starparser --i run_data.star --count_mics -c _rlnMicrographName -q 200826
```

---

* Extract particles with defocus values (in \_rlnDefocusU) less than this value and write to a new file.

```
starparser --i run_data.star --o output.star --max_defocus 40000
```

---

* Extract particles with defocus values (in \_rlnDefocusU) less than this value that also have "200826" in the \_rlnMicrographName column, and write to a new file.

```
starparser --i run_data.star --o output.star --max_defocus 40000 -c _rlnMicrographName -q 200826
```

---

* List all micrographs in the star file to a new text file.

```
starparser --i run_data.star --list_column _rlnMicrographName
```

---

* List all defocus values and x-coordinate values in the star file to new text files.

```
starparser --i run_data.star --list_column _rlnDefocusU/_rlnCoordinateX
```

---

* List all defocus values of particles that contain "200826" in the \_rlnMicrographName column.

```
starparser --i run_data.star --list_column _rlnDefocusU -c _rlnMicrographName -q 200826
```

---

* Swap the following columns from file2.star into run_data.star: \_rlnAnglePsi, \_rlnAngleRot, \_rlnAngleTilt, \_rlnNormCorrection, \_rlnLogLikeliContribution, \_rlnMaxValueProbDistribution, \_rlnNrOfSignificantSamples, \_rlnOriginXAngst, \_rlnOriginYAngst.

```
starparser --i run_data.star --f file2.star --o output.star --swap_columns _rlnAnglePsi/_rlnAngleRot/_rlnAngleTilt/_rlnNormCorrection/_rlnLogLikeliContribution/_rlnMaxValueProbDistribution/_rlnNrOfSignificantSamples/_rlnOriginXAngst/_rlnOriginYAngst
```

---

* Relegate the star file to be compatible with Relion 3.0.

```
starparser --i run_data.star --o output.star --relegate
```

---


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
