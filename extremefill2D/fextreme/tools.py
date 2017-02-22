"""General tools not associated with extremefill
"""

from itertools import repeat, product
import os

import datreant.core as dtr
# pylint: disable=no-name-in-module, redefined-builtin
from toolz.curried import curry, pipe, last, map, get, compose, filter
import jinja2
import yaml


def get_by_uuid(uuid, path='.'):
    """Get a Treant by short ID

    Args:
      uuid: a portion of the uuid
      path: the search path for Treants

    Returns:
      a Treant

    >>> from click.testing import CliRunner
    >>> with CliRunner().isolated_filesystem() as dir_:
    ...     assert pipe(
    ...         dir_,
    ...         dtr.Treant,
    ...         lambda x: x.uuid == get_by_uuid(x.uuid[:8]).uuid)
    """
    return pipe(
        path,
        dtr.discover,
        list,
        filter(lambda x: uuid in x.uuid),
        list,
        get(0, default=None)
    )


@curry
def enum(func, seq):
    """Enumerate implementation of map.

    Args:
      func: function with (i, x) arguments
      seq: a sequence

    Returns:
      sequence of outputs from func
    """
    return pipe(
        enumerate(list(seq)),
        map(tlam(func)),  # pylint: disable=no-value-for-parameter
    )


def test_enum():
    """Test enum
    """
    assert pipe(
        ('a', 'b', 'c', 'd'),
        enum(lambda i, x: (i, x)),  # pylint: disable=no-value-for-parameter
        list,
        lambda x: x == [(0, 'a'), (1, 'b'), (2, 'c'), (3, 'd')]
    )


def latest(treant):
    """Get the latest data file available based on a sort.
    """
    return pipe(
        treant.glob('*.nc'),
        sorted,
        last,
        lambda leaf: leaf.abspath,
    )


@curry
def all_files(pattern, treant):
    """Get the sorted file paths in a Treant

    Args:
      pattern: a pattern match
      treant: a Treant object

    Returns:
      a list of file paths
    """
    return pipe(
        pattern,
        treant.glob,
        sorted,
        map(lambda leaf: leaf.abspath)
    )


@curry
def tlam(func, tup):
    """Split tuple into arguments
    """
    return func(*tup)


@curry
def render_yaml(tpl_path, **kwargs):
    """Return the rendered yaml template.

    Args:
      tpl_path: path to the YAML jinja template
      **kwargs: data to render in the template

    Retuns:
      the rendered template string
    """
    path, filename = os.path.split(tpl_path)
    loader = jinja2.FileSystemLoader(path or './')
    env = jinja2.Environment(loader=loader)
    env.filters['to_yaml'] = yaml.dump
    return env.get_template(filename).render(**kwargs)


def get_path(file_):
    """Return the local file path for this file.

    Returns:
      the filepath
    """
    return pipe(
        file_,
        os.path.realpath,
        os.path.split,
        get(0)
    )


def base_path():
    """Return the base path for the data directory.
    """
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..')


def fcompose(*args):
    """Helper function to compose functions.

    >>> f = lambda x: x - 2
    >>> g = lambda x: 2 * x
    >>> f(g(3))
    4
    >>> fcompose(g, f)(3)
    4

    Args:xb
      *args: tuple of funct]ions

    Retuns:
      composed functions
    """
    return compose(*args[::-1])


def outer_dict(dict_in):
    """Outer product of dictionary values

    Args:
      dict_in: a dictionary with iterable values

    Returns:
      a list of dictionaries

    >>> assert pipe(
    ...     dict(a=[1], b=[2, 3]),
    ...     curry(outer_dict),
    ...     lambda x: x == [dict(a=1, b=2), dict(a=1, b=3)]
    ... )
    """
    return pipe(
        dict_in.items(),
        lambda x: zip(*x),
        list,
        lambda x: (x[0], product(*x[1])),
        # pylint: disable=no-value-for-parameter
        tlam(lambda x, y: zip(repeat(x), y)),
        map(lambda x: zip(*x)),
        map(dict),
        list
    )


@curry
def set_treant_categories(dict_in, treant):
    """Set all the categories in a treant to dict values.

    Args:
      dict_in: the key value pairs
      treant: the treant

    Returns:
      the updated treant
    """
    return pipe(
        dict_in.items(),
        map(lambda x: treant.categories.__setitem__(x[0], x[1])),
        list,
        lambda _: treant
    )


def test_set_treant_categories():
    """Test set_treant_categories
    """
    from click.testing import CliRunner
    with CliRunner().isolated_filesystem() as dir_:
        assert pipe(
            dir_,
            dtr.Treant,
            # pylint: disable=no-value-for-parameter
            set_treant_categories(dict(a=1)),
            lambda x: x.categories['a'] == 1
        )


@curry
def ifexpr(fpredicate, ftrue, ffalse, arg):
    """Functional if expression.

    Args:
      fpredicate: true/false function on arg
      ftrue: run if fpredicate is true with arg
      ffalse: run if fpredicate is false with arg
      arg: the arg to run on the functions

    Returns:
      the result of either ftrue or ffalse
    """
    if fpredicate(arg):
        return ftrue(arg)
    else:
        return ffalse(arg)


def test_ifexpr():
    """Test ifexpr
    """
    func = ifexpr(lambda x: x > 2.5,  # pylint: disable=no-value-for-parameter
                  lambda x: x * 2,
                  lambda x: x / 2)
    assert func(2) == 1
    assert func(3) == 6
