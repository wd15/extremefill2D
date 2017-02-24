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
from toolz.curried import pipe, do, curry, juxt, map
from toolz.curried import iterate, nth, excepts, identity
import datreant.core

from .run_simulation import run
from .tools import latest, base_path, fcompose, ifexpr
from .tools import set_treant_categories, outer_dict


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
             tags=None,
             **extra_params):
    """Initialize a simulation.

    Args:
      jsonfile: the jsonfile to copy
      data_path: the path in which to make the treant
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
        set_treant_categories(extra_params),
        do(lambda treant: pipe(
            jsonfile,
            read_json,
            lambda params: {**params, **extra_params},
            save_json(os.path.join(treant.abspath, 'params.json'))
        )),
        do(lambda treant: read_run_save(
            treant['params.json'].abspath,
            treant['data0000000.nc'].abspath))
    )


def multi_init_sim(jsonfile, data_path, pmap, param_grid, tags=None):
    """Start multiple simulations.

    Args:
      jsonfile: the jsonfile base parameters
      data_path: the path in which to make the treants
      pmap: the map function to use (curried)
      param_grid: the parameter grid as a function
      tags: tags for the treants

    Returns:
      list of treants

    >>> with CliRunner().isolated_filesystem() as dir_:
    ...     assert pipe(
    ...         os.path.join(base_path(), 'scripts', 'params1.json'),
    ...         lambda x: multi_init_sim(x,
    ...                                  dir_,
    ...                                  map,
    ...                                  dict(bulkSuppressor=[-0.16, -0.18])),
    ...         map(lambda x: x.leaves.abspaths),
    ...         map(lambda x: map(os.path.basename, x)),
    ...         map(lambda x: 'params.json' in x),
    ...         curry(all)
    ...     )
    """
    return pipe(
        param_grid,
        outer_dict,
        pmap(lambda kwargs: init_sim(jsonfile,
                                     data_path,
                                     tags=tags,
                                     **kwargs)),
        list
    )


@curry
def run_save(params, total_steps, input_values, datapath):
    """Run and save a simulation
    """
    return pipe(
        params,
        run(total_steps=total_steps, input_values=input_values),
        xarray.Dataset,
        lambda data: data.to_netcdf(datapath),
        lambda _: None
    )


@curry
def read_run_save(jsonpath, datapath, total_steps=0, input_values=None):
    """Read a prams file and then run and save a simulation.
    """
    return pipe(
        jsonpath,
        read_json,
        lambda params: namedtuple('parameters', params.keys())(**params),
        excepts(RuntimeError,
                run_save(total_steps=total_steps,
                         input_values=input_values,
                         datapath=datapath),
                identity),
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
      an updated treant and an error

    """
    return pipe(
        latest(treant),
        juxt(xarray.open_dataset,
             lambda datafile: treant[next_datafile(datafile, steps)].abspath),
        lambda data: read_run_save(
            treant['params.json'].abspath,
            data[1],
            total_steps=steps,
            input_values=data[0]),
        lambda error: (treant, error)
    )


@curry
def restart_sim_iter(treant_and_error, steps):
    """Restart an iterative simulation.

    Runs the simulation if the error is None.

    Args:
      treant_and_error: a tuple of (treant, error)
      steps: the number of stpes to execute

    Returns:
      a treant, error pair

    """
    return pipe(
        treant_and_error,
        ifexpr(lambda x: x[1] is None,
               lambda x: restart_sim(x[0], steps),
               identity)
    )


@curry
def iterate_sim(treant, iterations, steps):
    """Iterate a simulation multiple times

    Args:
      treant: the data store treant
      iterations: total time steps is iterations * steps
      steps: the number of steps per iteration

    Returns:
      an updated treant
    """
    return pipe(
        (treant, None),
        iterate(restart_sim_iter(steps=steps)),
        nth(iterations)
    )


def test_iterate_sim():
    """Test iterate_sim
    """
    with CliRunner().isolated_filesystem() as dir_:
        assert pipe(
            os.path.join(base_path(), 'scripts', 'params.json'),
            init_sim(data_path=dir_),
            iterate_sim(iterations=1, steps=10),
            lambda x: x[0].leaves.abspaths,
            map(os.path.basename),
            lambda data: 'data0000010.nc' in data,
        )


def test_restart_sim():
    """Test restart_sim
    """
    with CliRunner().isolated_filesystem() as dir_:
        assert pipe(
            os.path.join(base_path(), 'scripts', 'params.json'),
            init_sim(data_path=dir_),
            restart_sim(steps=10),
            lambda x: x[0].leaves.abspaths,
            map(os.path.basename),
            lambda data: 'data0000010.nc' in data,
        )
