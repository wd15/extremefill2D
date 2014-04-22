import json
from collections import namedtuple


import tables
import numpy as np
from extremefill2D.systems import ExtremeFillSystem, ConstantCurrentSystem
from extremefill2D.meshes import ExtremeFill2DMesh

def assert_close(v1, v2):
    print v1, v2
    assert np.allclose(v1, v2)

def read_params(jsonfile='params.json', **kwargs):
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
    params = read_params(jsonfile='constant_current.json', totalSteps=1, sweeps=50)
    system = ConstantCurrentSystem(params)
    system.run()
    assert_close(float(system.variables.current), params.current)

def test_mesh():
    params = read_params()
    mesh = ExtremeFill2DMesh(params)
    dx = mesh.get_nonuniform_dx(0.1, 3.0, 4.0, 10.0, 0.3, 2.0)
    assert_close(np.sum(dx[:7]), 3.0)
    solution = [ 2. ,  0.4,  0.2,  0.1,  0.1,  0.1,  0.1,  0.1,  0.1,  0.1,  0.1, 
                 0.1,  0.1,  0.1,  0.1,  0.1,  0.1,  0.1,  0.1,  0.1,  0.1,  0.2,
                 0.4,  0.8,  4.2]
    assert_close(dx, solution)

def test_mesh_via():
    params = read_params()
    mesh = ExtremeFill2DMesh(params)
    x2 = 3.0
    dx = mesh.get_nonuniform_dx(0.2, 0.0, 1.0, x2, 0.4, 2.0)
    assert_close(np.sum(dx), x2)
    assert_close(len(dx), 9)

def test_goemtery():
    params = read_params()
    mesh = ExtremeFill2DMesh(params)
    spacing = mesh.geometric_spacing(1., 10., 1.1)
    solution = [ 1.     ,  1.1    ,  1.21   ,  1.331  ,  1.4641 ,  1.61051,  2.28439]
    assert_close(spacing, solution)
    assert_close(np.sum(spacing), 10.0)

def test_hemispherical_cap():
    params = read_params(jsonfile='constant_current.json', totalSteps=1, sweeps=10, cap_radius=3.75e-5)
    system = ConstantCurrentSystem(params)
    system.run()
    mesh = system.distance.mesh
    center =(0.0, params.delta)
    radius = np.sqrt((mesh.x - center[0])**2 + (mesh.y - center[1])**2)
    mask = np.array(radius < params.cap_radius)
    assert_close(np.array(system.variables.cupric)[mask], params.bulkCupric)
    
if __name__ == '__main__':
    test_hemispherical_cap()
