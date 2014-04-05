import sys
import os
import tempfile
import json


import tables
import numpy as np


def assert_close(v1, v2):
    import sys
    print v1, v2
    assert np.allclose(v1, v2)

    
class ScriptSetup(object):
    def __init__(self, script, params, jsonfile=None):
        self.script = script
        self.new_params(params, jsonfile)
        
    def __enter__(self):
        rmdatafile = os.path.join('Data', 'data.h5')
        if os.path.exists(rmdatafile):
            os.remove(rmdatafile)
        self.tmpjsonfile = self.write_params()
        self.argv = list(sys.argv)
        sys.argv = [self.script, self.tmpjsonfile]
        return self
        
    def __exit__(self, *args):
        sys.argv = self.argv
        os.remove(self.tmpjsonfile)

    def new_params(self, params, jsonfile=None):
        if not jsonfile:
            jsonfile = os.path.splitext(self.script)[0] + '.json'
        with open(jsonfile, 'rb') as f:
            params_dict = json.load(f)
        for k, v in params.iteritems():
            params_dict[k] = v
        self.params_dict = params_dict

    def write_params(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            json.dump(self.params_dict, f)
            tmpjsonfile = f.name
        return tmpjsonfile

    
class BaseClass(object):
    def __init__(self, params):
        with ScriptSetup('annular.py', params):
            import annular
        self.data = self.get_data(annular)
        self.other_data = self.get_other_data(annular)
        del sys.modules['annular']
        
    def test(self):
        for k, v in self.data.iteritems():
            o = self.other_data[k]
            yield assert_close, v, o
        
    
class TestAnnular(BaseClass):
    def __init__(self):
        self.attrs = ['distance', 'potential', 'theta', 'suppressor', 'cupric']
        params = {'totalSteps' : 5}
        super(TestAnnular, self).__init__(params)

    def get_data(self, module):
        return dict((attr, getattr(module.variables, attr)) for attr in self.attrs)
    
    def get_other_data(self, module):
        datafile = 'annular.h5'
        h5file = tables.openFile(datafile, mode='r')
        index = h5file.root._v_attrs.latestIndex
        datadict = h5file.getNode('/ID' + str(int(index)))
        data = dict()
        for attr in self.attrs:
            data[attr] = getattr(datadict, attr).read()
        h5file.close()
    
        return data
        

class TestConstantCurrent(BaseClass):
    def __init__(self):
        params = {'totalSteps' : 1,
                  'constant_current' : True,
                  'sweeps' : 50}
        super(TestConstantCurrent, self).__init__(params)

    def get_data(self, module):
        return {'current' : float(module.variables.current)}

    def get_other_data(self, module):
        return {'current' : module.params.current}

    #t = TestConstantCurrent()
    #print np.allclose(t.data['current'], t.other_data['current'])

