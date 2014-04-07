import json
from collections import namedtuple


import tables
import numpy as np
from extremefill2D.systems import ExtremeFillSystem, ConstantCurrentSystem


def assert_close(v1, v2):
    print v1, v2
    assert np.allclose(v1, v2)

def read_params(**kwargs):
    jsonfile = 'params.json'
    with open(jsonfile, 'rb') as ff:
        params_dict = json.load(ff)
    for k, v in kwargs.iteritems():
        params_dict[k] = v
    return namedtuple('ParamClass', params_dict.keys())(*params_dict.values())

def read_data(attrs):
    datafile = 'annular.h5'
    h5file = tables.openFile(datafile, mode='r')
    index = h5file.root._v_attrs.latestIndex
    datadict = h5file.getNode('/ID' + str(int(index)))
    data = dict()
    for attr in attrs:
        data[attr] = getattr(datadict, attr).read()
    h5file.close()
    return data

def test():
    params = read_params(totalSteps=5)
    system = ExtremeFillSystem(params)
    system.run()
    attrs = ['distance', 'potential', 'theta', 'suppressor', 'cupric']
    data = dict((attr, getattr(system.variables, attr)) for attr in attrs)
    data_other = read_data(attrs)
    for k, v in data.iteritems():
        o = data_other[k]
        yield assert_close, v, o
        
def test_constant_current():
    params = read_params(totalSteps=1, sweeps=50)
    system = ConstantCurrentSystem(params)
    system.run()
    assert_close(float(system.variables.current), params.current)

