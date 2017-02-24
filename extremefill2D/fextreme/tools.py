"""General tools not associated with extremefill
"""
# pylint: disable=no-value-for-parameter

from itertools import repeat, product
import os

import datreant.core as dtr
# pylint: disable=no-name-in-module, redefined-builtin
from toolz.curried import curry, pipe, last, map, get, compose, filter, merge
import jinja2
import yaml
import pandas


@curry
def get_by_uuid(uuid, path='.'):
    """Get a Treant by short ID

    Args:
      uuid: a portion of the uuid
      path: the search path for Treants

    Returns:
      a Treant

    """
    return pipe(
        path,
        dtr.discover,
        list,
        filter(lambda x: uuid in x.uuid),
        list,
        get(0, default=None)
    )

def test_get_by_uuid():
    """Test get_by_uuid
    """
    from click.testing import CliRunner
    with CliRunner().isolated_filesystem() as dir_:
        assert pipe(
            dir_,
            dtr.Treant,
            lambda x: x.uuid == get_by_uuid(x.uuid[:8]).uuid)


@curry
def get_by_tags(tags, path='.'):
    """Get a Treant by tags

    Args:
      tags: the identifying tags
      path: the base path to the treants

    Retuns:
      a bundle of treants
    """
    return pipe(
        path,
        dtr.discover,
        lambda x: x[x.tags[tuple(tags)]],
    )


def get_treant_data(treant):
    """Extract UUID, tags and categories as a dict from Treant.

    Args:
      treant: the treant to extract data from

    Returns:
      a dict of treant data
    """
    return merge(
        dict(uuid=treant.uuid[:8], tags=list(treant.tags)),
        dict(treant.categories)
    )


def get_treant_df(tags, path='.'):
    """Get treants as a Pandas DataFrame

    Args:
      tags: treant tags to identify the treants
      path: the path to search for treants

    Returns:
      a Pandas DataFrame with the treant name, tags and categories

    >>> from click.testing import CliRunner
    >>> from toolz.curried import do
    >>> with CliRunner().isolated_filesystem() as dir_:
    ...     assert pipe(
    ...         dir_,
    ...         dtr.Treant,
    ...         do(lambda x: x.__setattr__('tags', ['atag'])),
    ...         lambda x: x.uuid[:8],
    ...         lambda x: x == get_treant_df(['atag'], path=dir_).uuid[0]
    ...     )
    """
    return pipe(
        tags,
        get_by_tags(path=path),
        lambda x: x.map(get_treant_data),
        pandas.DataFrame,

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
        map(tlam(func)),
    )


def test_enum():
    """Test enum
    """
    assert pipe(
        ('a', 'b', 'c', 'd'),
        enum(lambda i, x: (i, x)),
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
    func = ifexpr(lambda x: x > 2.5,
                  lambda x: x * 2,
                  lambda x: x / 2)
    assert func(2) == 1
    assert func(3) == 6


@curry
def pmap(client, func, data):
    """Map with a parallel client.

    Args:
      client: a parallel client with a map and result method
      func: the function to map
      data: the data to map over

    Returns:
      the result of the mapping
    """
    return pipe(
        client.map(func, data),
        map(lambda x: x.result()),
        list
    )


def test_pmap():
    """Test pmap
    """
    # pylint: disable=missing-docstring, too-few-public-methods
    class DummyResult:
        def __init__(self, result):
            self._result = result

        def result(self):
            return self._result

    # pylint: disable=too-few-public-methods, missing-docstring
    class DummyClient:
        def map(self, func, data):  # pylint: disable=no-self-use
            return pipe(
                data,
                map(func),
                map(DummyResult),
                list
            )

    assert [2, 4] == pmap(DummyClient())(lambda x: x * 2, [1, 2])
