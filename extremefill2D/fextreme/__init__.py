"""Functional implementation of the extremefill2D code.
"""

import os
import tempfile
import json
from collections import namedtuple
import xarray

import numpy as np
from toolz.curried import pipe, compose, do, curry # pylint: disable=no-name-in-module

from ..contourViewer import ContourViewer
from .run_simulation import run

import datreant.core


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

# def make_object(dict_):
#     """The ExtremeFillSystem requires a namedtuple
#     """
#     return namedtuple("ParamClass", dict_.keys())(*dict_.values())

def read_params(jsonfile):
    """Read a json file into a dictionary
    """
    with open(jsonfile, 'r') as filepointer:
        dict_ = json.load(filepointer)
    return dict_

# def contour_plot(args):
#     """Plot a contour plot given a filename and the parameters.
#     """
#     datafile, params = args
#     viewer = ContourViewer(datafile, indexJump=params.data_frequency, featureDepth=65e-6)
#     return viewer.plot(indices=np.arange(0, params.totalSteps, params.data_frequency))

# def copy_file(params):
#     """Required to deal with stale open file issues
#     """
#     tmp = 'tmp.h5'
#     shutil.copy(params.datafile, 'tmp.h5')
#     return (tmp, params)

def make_new_treant(base_dir='data'):
    return pipe(
        tempfile.mkdtemp(dir=base_dir),
        datreant.core.Treant,
        do(lambda x: x.__setattr__('name', x.uuid)),
    )

def save_to_json(filepath, data):
    with open(filepath, 'w') as fpointer:
        json.dump(data, fpointer)

@curry
def save_xarray(filepath, data):
    data.to_netcdf(filepath)

@curry
def save(data, filepath, savefunc, treant=None):
    return pipe(
        treant or make_new_treant(),
        do(lambda treant: savefunc(treant[filepath].makedirs().abspath, data))
    )

@curry
def run_and_save(treant, steps, datafile='data.nc'):
    return pipe(
        treant['params.json'].abspath,
        read_params,
        lambda params: namedtuple('parameters', params.keys())(**params),
        run(total_steps=steps),
        xarray.Dataset,
        lambda data: data.to_netcdf(treant[datafile].abspath),
        lambda _: treant
    )

def main(jsonfile, tags=[], **extra_params):
    """Run a simulation and get the datreant ID.
    """
    return pipe(
        jsonfile,
        read_params,
        lambda x: {**x, **extra_params},
        save(filepath='params.json', savefunc=save_to_json),
        do(lambda x: x.__setattr__('tags', tags)),
        run_and_save(steps=0),
    )



        # lambda x: dict(treant=make_treant(tags), )make_object(x['params'])
        # do(lambda x: os.remove(x.datafile) if os.path.exists(x.datafile) else None),
        # do(run_from_treant),
        # copy_file,
        # contour_plot)
