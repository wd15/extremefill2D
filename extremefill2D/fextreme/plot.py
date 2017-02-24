"""Functions to plot a vega plot from Extremefill data
"""
# pylint: disable=no-value-for-parameter

import os

import numpy as np
from skimage import measure
import xarray
# pylint: disable=redefined-builtin, no-name-in-module
from toolz.curried import pipe, juxt, valmap, concat, map
from scipy.interpolate import griddata
import pandas
import yaml
import vega

from .tools import tlam, enum, render_yaml, get_path, all_files


def vega_plot_treant(treant):
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
    ...          vega_plot_treant,
    ...          lambda x: type(x) is vega.Vega)
    """
    return vega_plot_treants([treant])


def vega_plot_treants(treants):
    """Make a vega plot with multiple treants

    Args:
      treants: a list of treants

    Returns:
      a vega.Vega type
    """
    return pipe(
        treants,
        enum(lambda i, x: vega_contours(x, counter=i)),
        concat,
        list,
        lambda x: render_yaml(os.path.join(get_path(__file__),
                                           'templates',
                                           'vega.yaml.j2'),
                              data=x,
                              title=treants[0].uuid[:8]),
        yaml.load,
        vega.Vega
    )


def vega_contours(treant, counter=0):
    """
    Get the contours as Vega data.

    Args:
      treant: a Treant object with data files

    Returns:
      contours formatted as Vega data
    """
    return pipe(
        treant,
        all_files('*.nc'),
        map(contours_from_datafile),
        concat,
        map(pandas.DataFrame),
        map(lambda x: x.rename(columns={0: 'x', 1: 'y'})),
        map(lambda x: x.to_dict(orient='records')),
        map(map(valmap(float))),
        map(list),
        enum(lambda i, x: dict(name='contour_data{0}_{1}'.format(i, counter),
                               values=x)),
    )


def contours_from_datafile(datafile):
    """Calculate the contours given a netcdf datafile

    Args:
      datafile: the netcdf datafile

    Returns:
      a list of contours
    """
    return pipe(
        datafile,
        xarray.open_dataset,
        lambda x: dict(x=x.x.values,
                       y=x.y.values,
                       z=x.distance.values,
                       dx=x.nominal_dx),
        contours
        )


def contours(data):
    """Get zero contours from x, y, z data

    Args:
      data: dictionary with (x, y, z, dx) keys

    Returns:
      a list of (N, 2) numpy arrays representing the contours
    """
    def linspace_(arr, spacing):
        """Calcuate the linspace based on a spacing
        """
        return pipe(
            arr,
            juxt(min, max),
            tlam(lambda x_, y_: np.linspace(x_, y_, (y_ - x_) / spacing))
        )

    return pipe(
        data,
        lambda x: dict(xi=linspace_(x['x'], x['dx']),
                       yi=linspace_(x['y'], x['dx']),
                       **x),
        lambda x: griddata((x['y'], x['x']),
                           x['z'],
                           (x['yi'][None, :], x['xi'][:, None]),
                           method='cubic'),
        lambda x: measure.find_contours(x, 0.0),
        map(lambda x: float(data['dx']) * x)
    )
