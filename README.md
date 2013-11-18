# Extreme Fill 2D

## Overview

This repository contains all the code necessary to reproduce the
simulations for the Extreme Fill 2D model described in a
[paper](#paper) by Wheeler, Moffat and Josell recently submitted to
the JES. A
[recent blog post](http://wd15.github.io/2013/05/07/extremefill2d/)
shows a movie from a simulation as well as a description of Extreme
Fill.

## Sumatra

The simulation data used to produce the images was generated using the
Sumatra simulation management tool. The goal is to make the simulation
data and the simulation records available publicly. However, at the
time of writing the data is currently not public.

## Paper

Temporal and Spatial Modeling of Extreme Bottom-Up Filling of Through
Silicon Vias, D. Wheeler, T. P. Moffat and D. Josell, submitted to the
Journal of the Electrochemical Society (2013).

Unfortunately, I was unable the upload the paper to a preprint service
due to issues with the Journal.

## License

The repository is licensed with the FreeBSD License, see
[LICENSE.txt](LICENSE.txt).

## Requirements

The [REQUIREMENTS.txt](REQUIREMENTS.txt) file has a complete list of
packages in the Python environment during development. The most
important of these are listed. The version numbers are mostly not
important within reason, but if you have problems the version numbers
may help.

 * FiPy dev version `6e897df400`
 * IPython dev version `b31eb2f2d9`
 * Matplotlib 1.2.1
 * Numpy 1.7.1
 * Pandas 0.12.0
 * Scipy 0.13.0
 * Tables 2.4.0
 * Cython==0.19.1
 * Sumatra dev version `3c00d7ccfb`
 * Brewer2mpl 1.3.1
 * Prettyplotlib 0.1.3
 * Pylsmlib==0.1
 * Scikit-fmm dev version `78a243dd9d`
 
## Citing the Notebooks and Images

The plan is to either add a citable DOI for the entire project or for
each individual notebook via Figshare.

## AMI

An Amazon Machine Image of the software to reproduce the simulations
and build the figures will be launched soon.

## Authors

 * [Daniel Wheeler](http://wd15.github.io/about.html)
 * [Tom Moffat](http://www.nist.gov/mml/msed/thomas_moffat.cfm)
 * [Daniel Josell](http://www.nist.gov/mml/msed/daniel-josell.cfm)
