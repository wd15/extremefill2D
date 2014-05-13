# Extreme Fill 2D

## Overview

This repository contains all the code necessary to reproduce the
simulations for the Extreme Fill 2D model described in a
[paper](#paper) by Wheeler, Moffat and Josell recently submitted to
the JES. For further details on Extreme Fill see this
[recent blog post](http://wd15.github.io/2013/05/07/extremefill2d/)
and read the [paper](#paper). The repository aims to make both the
simulations and the images entirely reproducible.

## Sumatra

The simulations used to produce the images in the paper were managed
using the [Sumatra](http://pythonhosted.org/Sumatra/) simulation
management tool. Sumatra has a web server for displaying the
simulation records. Using this server, the plan is to have a publicly
available database of simulation meta-data records as well as publicly
available simulation data files. Sumatra setup:

    $ smt init --store=postgres://wd15:"Ji9waeRe3io@"@dromio.nist.gov/wd15 extremefill2D
    $ smt configure --executable=python --main=script.py
    $ smt configure -g uuid
    $ smt configure -c store-diff
    $ smt configure --addlabel=parameters

## Paper

Temporal and Spatial Modeling of Extreme Bottom-Up Filling of Through
Silicon Vias, D. Wheeler, T. P. Moffat and D. Josell, submitted to the
Journal of the Electrochemical Society (2013).

Unfortunately, I was unable the upload the paper to a preprint service
due to issues with the Journal.

## Notebooks

The IPython notebooks can be viewed at
[nbviewer.ipython.org](http://nbviewer.ipython.org/github/wd15/extremefill2D/tree/master/notebooks).

## License

The repository is licensed with the FreeBSD License, see
[LICENSE.txt](LICENSE.txt).

## Requirements

The [REQUIREMENTS.txt](REQUIREMENTS.txt) file has a complete list of
packages active in the Python environment during development. The most
important of these are listed below. The version numbers should not be
important, but if you have problems the version numbers may help.

 * FiPy dev version `6e897df400`
 * IPython dev version `b31eb2f2d9`
 * Matplotlib 1.2.1
 * Numpy 1.7.1
 * Pandas 0.12.0
 * Scipy 0.13.0
 * Tables 2.4.0
 * Cython 0.19.1
 * Sumatra dev version `3c00d7ccfb`
 * Brewer2mpl 1.3.1
 * Prettyplotlib 0.1.3
 * Pylsmlib 0.1
 * Scikit-fmm dev version `78a243dd9d`
 
## Citing the Notebooks and Figures

The plan is to either add a citable DOI for each individual notebook
using Figshare.

## AMI

An Amazon Machine Image of the entire stack to reproduce the images
and simulations will be launched soon.

## Authors

 * [Daniel Wheeler](http://wd15.github.io/about.html)
 * [Tom Moffat](http://www.nist.gov/mml/msed/thomas_moffat.cfm)
 * [Daniel Josell](http://www.nist.gov/mml/msed/daniel-josell.cfm)
