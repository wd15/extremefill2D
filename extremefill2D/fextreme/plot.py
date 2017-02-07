"""Functions to plot a vega plot from Extremefill data
"""
import os

import numpy as np
from skimage import measure
import xarray
from toolz.curried import pipe, juxt, map, valmap # pylint: disable=redefined-builtin, no-name-in-module
from scipy.interpolate import griddata
import pandas
import yaml
import vega

from .tools import latest, tlam, enum, render_yaml, get_path


def vega_plot(treant):
    """Make a vega plot

    Args:
      treant: a treant

    Returns
      a vega.Vega type

    >>> from click.testing import CliRunner
    >>> from extremefill2D.fextreme import init_sim
    >>> from extremefill2D.fextreme.tools import base_path
    >>> with CliRunner().isolated_filesystem() as dir_:
    ...      assert pipe(
    ...          os.path.join(base_path(), 'scripts', 'params.json'),
    ...          init_sim(data_path=dir_),
    ...          vega_plot,
    ...          lambda x: type(x) is vega.Vega)
    """
    return pipe(
        treant,
        get_data,
        list,
        lambda x: render_yaml(os.path.join(get_path(__file__),
                                           'templates',
                                           'vega.yaml.j2'),
                              data=x),
        yaml.load,
        vega.Vega
    )


def get_data(treant):
    """Generate a vega contour plot

    Args:
      treant: a treant object with the requisite data

    Returns:
      a list of (N, 2) numpy arrays representing the contours
    """
    return pipe(
        latest(treant),
        xarray.open_dataset,
        lambda x: dict(x=x.x.values,
                       y=x.y.values,
                       z=x.distance.values,
                       dx=x.nominal_dx),
        get_contours_,
        map(pandas.DataFrame),
        map(lambda x: x.rename(columns={0: 'x', 1: 'y'})),
        map(lambda x: x.to_dict(orient='records')),
        map(map(valmap(float))),
        map(list),
        enum(lambda i, x: dict(name='contour_data{0}'.format(i),   # pylint: disable=no-value-for-parameter
                               values=x)),
    )

def get_contours_(data):
    """Get the contours for plotting

    Args:
      data: dictionary with (x, y, z, dx) keys

    Returns:
      a list of (N, 2) numpy arrays representing the contours
    """
    linspace_ = lambda x: pipe(
        x,
        juxt(min, max),
        tlam(lambda x_, y_: np.linspace(x_, y_, (y_ - x_) / data['dx']))  # pylint: disable=no-value-for-parameter
    )
    return pipe(
        data,
        lambda x: dict(xi=linspace_(x['x']),
                       yi=linspace_(x['y']),
                       **x),
        lambda x: griddata((x['x'], x['y']),
                           x['z'],
                           (x['xi'][None, :], x['yi'][:, None]),
                           method='cubic'),
        lambda x: measure.find_contours(x, 0.0),
        map(lambda x: float(data['dx']) * x)
    )
