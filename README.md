# StarParser

Use this script to manipulate Relion 3.1 star files.

Usage:

```
python3 starparser.py --i input.star [options]
```

## Getting Started

* You need to have **Python 3** installed and have the **pandas** and **optparse** packages.

* Your file needs to be a standard **Relion 3.1** star file with an optics table, particle table, and particle list with tab delimited columns, (i.e. any Relion 3.1 output).

## Options

* ```--plot_defocus``` Plot defocus to Defocus_histogram.png. Can be used with -c and -q for a subset, otherwise plots all.

* ```--delete_column``` Delete column and renumber headers. E.g. \_rlnMicrographName. To enter multiple columns, separate them with a slash: \_rlnMicrographName/\_rlnCoordinateX.

* ```--delete_particles``` Delete particles. Pick a column header (-c) and query (-q) to delete particles that match it.

* ```--extract_particles``` Write a star file with particles that match a column header (-c) and query (-q).

* ```--count_particles``` Count particles and print the result. Can be used with -c and -q for a subset count, otherwise counts all.

* ```--count_mics``` Count the number of unique micrographs. Can be used with -c and -q for a subset count, otherwise counts all.

* ```--max_defocus``` Extract particles with defocus values less than this value (Angstroms). Can be used with -c and -q to only consider a subset.

* ```--list_column``` Write all values of a column to a file (filename is the header). E.g. \_rlnMicrographName. To enter multiple columns, separate them with a slash: \_rlnMicrographName/\_rlnCoordinateX. Can be used with -c and -q for a subset count, otherwise lists all items.

* ```--swap_columns``` Swap columns from another star file (specified with -f). E.g. \_rlnMicrographName. To enter multiple columns, separate them with a slash: \_rlnMicrographName/\_rlnCoordinateX.

* ```--relegate``` Remove optics table and optics column. This may not be sufficient to be fully compatible with Relion 3.0. Use --delete_column to remove other bad columns before this, if necessary.

* ```-f``` Name of second file to extract columns from.

* ```-c``` Column query. E.g. \_rlnMicrographName. To enter multiple columns, separate them with a slash: \_rlnMicrographName/\_rlnCoordinateX.

* ```-q``` Particle query. To enter multiple queries, separate them with a slash: 20200101/20200203.

* ```-o``` Output file name. Default is output.star.

## Examples

* Plot a histogram of defocus values.

```
python3 starparser.py --i run_data.star --plot_defocus
```

* Plot a histogram of defocus values from a subset of micrographs that contain "200826" or "200827".

```
python3 starparser.py --i run_data.star --plot_defocus -c _rlnMicrographName -q 200826/200827
```

* Delete the \_rlnCtfMaxResolution and \_rlnCtfFigureOfMerit columns.

```
python3 starparser.py --i run_data.star --delete_column _rlnCtfMaxResolution/_rlnCtfFigureOfMerit -o output.star
```

* Delete all particles with "200702" or "200715" in the \_rlnMicrographName column.

```
python3 starparser.py --i run_data.star --delete_particles -c _rlnMicrographName -q 200702/200715 -o output.star
```

* Make a new star file with only particles that have "1" in the \_rlnClassNumber column.

```
python3 starparser.py --i run_data.star --extract_particles -c _rlnClassNumber -q 1 -o output.star
```

* Count the number of particles with "200702" or "200715" in the \_rlnMicrographName column.

```
python3 starparser.py --i run_data.star --count_particles -c _rlnMicrographName -q 200702/200715 -o output.star
```

* Count the total number of unique micrographs.

```
python3 starparser.py --i run_data.star --count_mics
```

* Count the total number of unique micrographs in the subset that contain "200826" in the \_rlnMicrographName column.

```
python3 starparser.py --i run_data.star --count_mics -c _rlnMicrographName -q 200826
```
* Extract particles with defocus values (in \_rlnDefocusU) less than this value and write to a new file.

```
python3 starparser.py --i run_data.star --max_defocus 40000 -o output.star
```
* Extract particles with defocus values (in \_rlnDefocusU) less than this value that also have "200826" in the \_rlnMicrographName column, and write to a new file.

```
python3 starparser.py --i run_data.star --max_defocus 40000 -c _rlnMicrographName -q 200826 -o output.star
```
* List all micrographs in the star file to a new text file.

```
python3 starparser.py --i run_data.star --list_column _rlnMicrographName
```

* List all defocus values and x-coordinate values in the star file to new text files.

```
python3 starparser.py --i run_data.star --list_column _rlnDefocusU/_rlnCoordinateX
```

* List all defocus values of particles that contain "200826" in the \_rlnMicrographName column.

```
python3 starparser.py --i run_data.star --list_column _rlnDefocusU -c _rlnMicrographName -q 200826
```

* Swap the \_rlnAnglePsi, \_rlnAngleRot, \_rlnAngleTilt, \_rlnNormCorrection, \_rlnLogLikeliContribution, \_rlnMaxValueProbDistribution, \_rlnNrOfSignificantSamples, \_rlnOriginXAngst, \_rlnOriginYAngst from file2.star into run_data.star

```
python3 starparser.py --i run_data.star --swap_columns _rlnAnglePsi/_rlnAngleRot/_rlnAngleTilt/_rlnNormCorrection/_rlnLogLikeliContribution/_rlnMaxValueProbDistribution/_rlnNrOfSignificantSamples/_rlnOriginXAngst/_rlnOriginYAngst -f file2.star -o output.star
```

* Relegate the star file to on compatible with Relion 3.0.

```
python3 starparser.py --i run_data.star --relegate -o output.star
```

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
