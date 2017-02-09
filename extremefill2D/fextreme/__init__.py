"""Functional implementation of the extremefill2D code.
"""

# pylint: disable=no-value-for-parameter

import os
import tempfile
import json
from collections import namedtuple
import re

from click.testing import CliRunner
import xarray
# pylint: disable=no-name-in-module, redefined-builtin
from toolz.curried import pipe, do, curry, juxt, map, iterate, nth
import datreant.core

from .run_simulation import run
from .tools import latest, base_path, fcompose


def read_json(jsonfile):
    """Read a json file into a dictionary

    Args:
      jsonfile: the name of the json file to read

    Returns:
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


@curry
def make_new_treant(base_dir='.'):
    """Create a treant with a unique ID

    Args:
      base_dir: the location of the treant

    Returns:
      a treant

    """
    return pipe(
        tempfile.mkdtemp(dir=base_dir),
        datreant.core.Treant,
        do(lambda x: x.__setattr__('name', x.uuid)),
    )


def test_make_new_treant():
    """Test make_new_treant
    """
    with CliRunner().isolated_filesystem():
        treant = make_new_treant(base_dir='.')
    assert treant.name == treant.uuid


@curry
def save_json(filepath, data):
    """Save an object to a JSON file

    Args:
      filepath: path to JSON file
      data: the object to save
    """
    with open(filepath, 'w') as fpointer:
        json.dump(data, fpointer)


@curry
def save(data, filepath, savefunc, base_dir='.', treant=None):
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
        treant or make_new_treant(base_dir=base_dir),
        do(lambda treant: savefunc(treant[filepath].makedirs().abspath, data))
    )


def test_save():
    """Test save
    """
    with CliRunner().isolated_filesystem():
        test = dict(a=1)
        treant = save(test, 'test.json', save_json)
        actual = read('test.json', read_json, treant)
        assert test == actual


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
def init_sim(jsonfile,
             data_path,
             init_datafile='data0000000.nc',
             tags=None,
             **extra_params):
    """Initialize a simulation.

    Args:
      jsonfile: the jsonfile to copy
      data_path: the path in which to make the treant
      init_datafile: the file for the intial data
      tags: tag this simulation
      **extra_params: parameters to change from the default

    Returns:
      the simulation treant

    """
    mkdirp = do(lambda x: None if os.path.exists(x) else os.makedirs(x))
    return pipe(
        data_path,
        mkdirp,
        make_new_treant,
        do(lambda treant: treant.__setattr__('tags',
                                             [] if tags is None else tags)),
        do(lambda treant: pipe(
            jsonfile,
            read_json,
            lambda params: {**params, **extra_params},
            # pylint: disable=no-value-for-parameter
            save_json(os.path.join(treant.abspath, os.path.basename(jsonfile)))
        )),
        do(lambda treant: run_and_save(
            treant[os.path.basename(jsonfile)].abspath,
            treant[init_datafile].abspath))
    )


def run_and_save(jsonpath, datapath, total_steps=0, input_values=None):
    """Run and save a simulation.
    """
    return pipe(
        jsonpath,
        read_json,
        lambda params: namedtuple('parameters', params.keys())(**params),
        run(total_steps=total_steps, input_values=input_values),
        xarray.Dataset,
        lambda data: data.to_netcdf(datapath)
    )


def test_init_sim():
    """Test init_sim
    """
    with CliRunner().isolated_filesystem() as dir_:
        assert pipe(
            os.path.join(base_path(), 'scripts', 'params.json'),
            init_sim(data_path=dir_),
            lambda treant: treant.leaves.abspaths,
            map(os.path.basename),
            lambda data: 'data0000000.nc' in data,
        )


def next_datafile(filename, steps):
    """Rename a file when using numbers to denote time steps.

    Adds steps to a filename of format abc010.abc.

    Args:
      filename: the filename, e.g. data0000100.nc
      steps: the number of steps

    Returns:
      an updated filename

    >>> next_datafile('file000.abc', 1)
    'file001.abc'
    >>> next_datafile('file_001.abc', 2)
    'file_003.abc'
    """
    return re.sub(
        r'\d+',
        fcompose(
            lambda obj: obj.group(0),
            juxt(int, len),
            lambda data: (str(data[0] + steps), data[1]),
            lambda data: data[0].zfill(data[1]),
        ),
        os.path.basename(filename),
        1
    )


@curry
def restart_sim(treant, steps):
    """Restart a simulation from the latest time step.

    Args:
      treant: the data store treant
      steps: the number of steps to execute

    Returns:
      an updated treant

    """
    return pipe(
        latest(treant),
        juxt(xarray.open_dataset,
             lambda datafile: treant[next_datafile(datafile, steps)].abspath),
        lambda data: run_and_save(
            treant['params.json'].abspath,
            data[1],
            total_steps=steps,
            input_values=data[0]),
        lambda _: treant
    )

def iterate_sim(treant, iterations, steps):
    """Iterate a simulation multiple times
    """
    return pipe(
        treant,
        iterate(restart_sim(steps=steps)),
        nth(iterations)
    )


def test_restart_sim():
    """Test restart_sim
    """
    with CliRunner().isolated_filesystem() as dir_:
        assert pipe(
            os.path.join(base_path(), 'scripts', 'params.json'),
            init_sim(data_path=dir_),
            restart_sim(steps=10),
            lambda treant: treant.leaves.abspaths,
            map(os.path.basename),
            lambda data: 'data0000010.nc' in data,
        )
