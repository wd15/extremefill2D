"""Functional implementation of the extremefill2D code.
"""

import shutil
import json
import os
from collections import namedtuple

import numpy as np
from toolz.curried import pipe, compose, do # pylint: disable=no-name-in-module

from ..contourViewer import ContourViewer
from .run_simulation import run


def fcompose(*args):
    """Helper function to compose functions.

    >>> f = lambda x: x - 2
    >>> g = lambda x: 2 * x
    >>> f(g(3))
    4
    >>> fcompose(g, f)(3)
    4

    Args:
      *args: tuple of functions

    Retuns:
      composed functions
    """
    return compose(*args[::-1])

def make_object(dict_):
    """The ExtremeFillSystem requires a namedtuple
    """
    return namedtuple("ParamClass", dict_.keys())(*dict_.values())

def read_params(jsonfile):
    """Read a json file into a dictionary
    """
    with open(jsonfile, 'r') as filepointer:
        dict_ = json.load(filepointer)
    return dict_

def contour_plot(args):
    """Plot a contour plot given a filename and the parameters.
    """
    datafile, params = args
    viewer = ContourViewer(datafile, indexJump=params.data_frequency, featureDepth=65e-6)
    return viewer.plot(indices=np.arange(0, params.totalSteps, params.data_frequency))

def copy_file(params):
    """Required to deal with stale open file issues
    """
    tmp = 'tmp.h5'
    shutil.copy(params.datafile, 'tmp.h5')
    return (tmp, params)

def main(jsonfile, datafile='data.h5', **extra_params):
    """Run a simulation and plot the results.
    """
    return pipe(
        jsonfile,
        read_params,
        lambda json_params: {'datafile' : datafile,
                             **json_params,
                             **extra_params},
        make_object,
        do(lambda x: os.remove(x.datafile) if os.path.exists(x.datafile) else None),
        do(run),
        copy_file,
        contour_plot)
