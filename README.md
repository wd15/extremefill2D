<h1> <p align="center"><sup><strong>
Extreme Fill 2D
</strong></sup></p>
</h1>

<p align="center">
<a href="https://travis-ci.org/wd15/extremefill2d" target="_blank">
<img src="https://api.travis-ci.org/wd15/extremefill2d.svg"
alt="Travis CI">
</a>
<a href="https://github.com/wd15/extremefill2D/blob/master/LICENSE.md">
<img src="https://img.shields.io/badge/license-mit-blue.svg" alt="License" height="18">
</a>
</p>

## Overview

This repository contains all the code necessary to reproduce the
simulations for the Extreme Fill 2D model described in a
[paper](https://dx.doi.org/10.1149/2.040312jes) by Wheeler, Moffat and
Josell submitted to the JES. For further details on Extreme Fill see
this
[recent blog post](http://wd15.github.io/2013/05/07/extremefill2d/)
and read the [paper](https://dx.doi.org/10.1149/2.040312jes). The
repository aims to make both the simulations and the images entirely
reproducible.

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

## License

The repository is licensed with the FreeBSD License, see
[LICENSE.txt](LICENSE.txt).
