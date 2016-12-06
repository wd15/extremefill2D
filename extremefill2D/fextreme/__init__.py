"""Functional implementation of the extremefill2D code.
"""

import os
import tempfile
import json
from collections import namedtuple

import xarray
from toolz.curried import pipe, compose, do, curry # pylint: disable=no-name-in-module
import datreant.core

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

def read_json(jsonfile):
    """Read a json file into a dictionary

    Args:
      jsonfile: the name of the json file to read

    Returns
      the contents of the JSON file as a dictionary

    >>> from click.testing import CliRunner
    >>> test = dict(a=1)
    >>> with CliRunner().isolated_filesystem():
    ...      filename = 'tmp.json'
    ...      save_json(filename, test)
    ...      assert test == read_json(filename)
    """
    with open(jsonfile, 'r') as filepointer:
        dict_ = json.load(filepointer)
    return dict_

def make_new_treant(base_dir='.'):
    """Create a treant with a unique ID

    Args:
      base_dir: the location of the treant

    Returns:
      a treant

    >>> from click.testing import CliRunner
    >>> with CliRunner().isolated_filesystem():
    ...     treant = make_new_treant(base_dir='.')
    ...     assert treant.name == treant.uuid
    """
    return pipe(
        tempfile.mkdtemp(dir=base_dir),
        datreant.core.Treant,
        do(lambda x: x.__setattr__('name', x.uuid)),
    )

def save_json(filepath, data):
    """Save an object to a JSON file

    Args:
      filepath: path to JSON file
      data: the object to save
    """
    with open(filepath, 'w') as fpointer:
        json.dump(data, fpointer)

@curry
def save(data, filepath, savefunc, treant=None):
    """Save data to a treant with callback

    Args:
      data: the data to save
      filepath: the filepath to save to
      savefunc: the save callback
      treant: the treant to save to, treant created if None

    Returns:
      the treant
    """
    return pipe(
        treant or make_new_treant(),
        do(lambda treant: savefunc(treant[filepath].makedirs().abspath, data))
    )

def test_save():
    """
    >>> from click.testing import CliRunner
    >>> with CliRunner().isolated_filesystem():
    ...     test = dict(a=1)
    ...     treant = save(test, 'test.json', save_json)
    ...     actual = read('test.json', read_json, treant)
    ...     assert test == actual
    """
    pass # pragma: no cover

@curry
def read(filepath, readfunc, treant):
    """Read data from a treant

    Args:
      filepath: the filepath to read from
      readfunc: the read callback
      treant: the treant to read from

    Returns:
      the data
    """
    return readfunc(treant[filepath].abspath)

@curry
def read_if_not_none(filepath, readfunc, treant):
    """Read data if filepath is not None

    Args:
      filepath: the filepath to read from
      readfunc: the read callback
      treant: the treant to read from

    Returns:
      the data or None
    """
    if filepath is None:
        return None
    else:
        return read(filepath, readfunc, treant)

@curry
def run_and_save(treant, steps, paramfile, write_cdf, read_cdf=None):
    """Run a simulation for save to a datafile

    Args:
      treant: the treant to read and write from
      steps: the number of steps to run
      write_cdf: the datafile to write to
      paramfile: the parameter file to read from
      read_cdf: the datafile to read from

    Returns:
      a treant with the simulation data
    """
    return pipe(
        treant[paramfile].abspath,
        read_json,
        lambda params: namedtuple('parameters', params.keys())(**params),
        run(total_steps=steps, # pylint: disable=no-value-for-parameter
            input_values=read_if_not_none(read_cdf, xarray.open_dataset, treant)),
        xarray.Dataset,
        lambda data: data.to_netcdf(treant[write_cdf].abspath),
        lambda _: treant
    )


def main(jsonfile, tags=None, steps=0, **extra_params):
    """Run a simulation and get the datreant ID.

    Args:
      jsonfile: the base parameters
      tags: tags to add to the data store for indentification
      extra_params: parameters to change from the base parameters

    Returns:
      the treant

    """
    return pipe(
        jsonfile,
        read_json,
        lambda x: {**x, **extra_params},
        save(filepath=os.path.basename(jsonfile), savefunc=save_json), # pylint: disable=no-value-for-parameter
        do(lambda x: x.__setattr__('tags', [] if tags is None else tags)),
        run_and_save(steps=steps,  # pylint: disable=no-value-for-parameter
                     paramfile=os.path.basename(jsonfile),
                     write_cdf='data0.nc'),
    )

def test_main():
    """
    >>> from click.testing import CliRunner
    >>> import shutil
    >>> param_filename = 'params.json'
    >>> current_path = os.path.dirname(os.path.abspath(__file__))
    >>> param_path = os.path.join(current_path, '../../scripts', param_filename)
    >>> with CliRunner().isolated_filesystem() as dir_:
    ...     new_param_path = shutil.copy(param_path, os.path.join(dir_, param_filename))
    ...     treant = main(new_param_path)
    ...     treant = run_and_save(treant=treant,
    ...                           steps=1,
    ...                           paramfile=param_filename,
    ...                           write_cdf='data1.nc',
    ...                           read_cdf='data0.nc')
    ...     assert treant['data0.nc'] in treant.leaves
    ...     assert treant['data1.nc'] in treant.leaves
    ...     treant = main(new_param_path, steps=2, shutdown_deposition_rate=1e+10)
    ...     treant = main(new_param_path, steps=3, dt=10.0, dtMin=1.0)
    """
    pass # pragma: no cover
