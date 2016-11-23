import json
from collections import namedtuple
import os


import tables
import numpy as np
from extremefill2D.systems import ExtremeFillSystem, ConstantCurrentSystem
from extremefill2D.meshes import ExtremeFill2DMesh


def assert_close(v1, v2, **kwargs):
    assert np.allclose(v1, v2, **kwargs)

def get_path():
    return os.path.split(__file__)[0]

def read_params(jsonfile=None, **kwargs):
    if jsonfile is None:
        jsonfile = os.path.join(get_path(), 'params.json')
    with open(jsonfile, 'r') as ff:
        params_dict = json.load(ff)
    for k, v in kwargs.items():
        params_dict[k] = v
    return namedtuple('ParamClass', params_dict.keys())(*params_dict.values())

def read_data(attrs):
    datafile = os.path.join(get_path(), 'annular.h5')
    h5file = tables.open_file(datafile, mode='r')
    index = h5file.root._v_attrs.latestIndex
    datadict = h5file.get_node('/ID' + str(int(index)))
    data = dict()
    for attr in attrs:
        data[attr] = getattr(datadict, attr).read()
    h5file.close()
    return data

def test():
    params = read_params(totalSteps=5)
    system = ExtremeFillSystem(params)
    system.run(print_data=False)
    attrs = ['distance', 'potential', 'theta', 'suppressor', 'cupric']
    data = dict((attr, getattr(system.variables, attr)) for attr in attrs)
    data_other = read_data(attrs)
    for k, v in data.items():
        o = data_other[k]
        L2 = np.sqrt(((v - o)**2).sum()) / len(o)
        assert np.allclose(v, o, rtol=1e-3, atol=1e-3) or (L2 < max(abs(v - o)))
        # yield assert_close, v, o

def constant_current_json():
    return os.path.join(get_path(), 'constant_current.json')

def test_constant_current():
    params = read_params(jsonfile=constant_current_json(), totalSteps=1, sweeps=50)
    system = ConstantCurrentSystem(params)
    system.run(print_data=False)
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
    params = read_params(jsonfile=constant_current_json(), totalSteps=1, sweeps=10, cap_radius=3.75e-5, dt=10.0)
    system = ConstantCurrentSystem(params)
    system.run(print_data=False)
    mesh = system.distance.mesh
    x = mesh.x.value
    y = mesh.y.value
    center =(0.0, max(y))
    radius = np.sqrt((x - center[0])**2 + (y - center[1])**2)
    mask = np.array(radius < params.cap_radius)
    value = np.array(system.variables.cupric)
    assert_close(value[mask], params.bulkCupric, rtol=1e-4)

    # min_mask = (x > 2e-5) & (x < 4e-5) & (y < params.rinner / 2.)
    # min_value = min(value[min_mask])
    # assert 650. < min_value < 750.

def test_hemispherical_cap_retreat():
    params = read_params(jsonfile=constant_current_json(), totalSteps=1, sweeps=10, cap_radius=3.75e-5, dt=10.0)
    system = ConstantCurrentSystem(params)
    system.run(print_data=False)
    assert np.sum(system.variables.cap.value) == 493
    phi = system.variables.distance
    phi.setValue(phi.value - params.router / 2.)
    assert np.sum(system.variables.cap.value) == 147
    phi.setValue(-1)
    assert np.sum(system.variables.cap.value) == 0

if __name__ == '__main__':
    test()
