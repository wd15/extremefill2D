"""Functions to plot a vega plot from Extremefill data
"""
import numpy as np
from skimage import measure
import xarray
from toolz.curried import pipe, juxt, map # pylint: disable=redefined-builtin, no-name-in-module
from scipy.interpolate import griddata

from .tools import latest, tlam


def get_contours(treant):
    """Get the contours for plotting

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
        get_contours_
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
        tlam(lambda x_, y_: np.linspace(x_, y_, (y_ - x_) / data['dx']))
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
        map(lambda x: float(data['dx']) * x),
        list
    )
