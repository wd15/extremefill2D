import sys
import os
import tempfile

import tables
import numpy as np


def test_annular():
    datafile = 'annular.h5'
    h5file = tables.openFile(datafile, mode='r')
    index = h5file.root._v_attrs.latestIndex
    data = h5file.getNode('/ID' + str(int(index)))
    
    rmdatafile = os.path.join('Data', 'data.h5')
    if os.path.exists(rmdatafile):
        os.remove(rmdatafile)

    script = 'annular.py'
    jsonfile = os.path.splitext(script)[0] + '.json'
    import json
    with open(jsonfile, 'rb') as f:
        params_dict = json.load(f)
    params_dict['totalSteps'] = 5

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        json.dump(params_dict, f)
        tmpjsonfile = f.name
    
            
    argv = list(sys.argv)
    sys.argv = ['annular.py', tmpjsonfile]

    import annular
        
    sys.argv = argv
    os.remove(tmpjsonfile)
    for attr in ['distance', 'potential', 'theta', 'suppressor', 'cupric']:
        test_value = getattr(data, attr).read()
        value = getattr(annular.variables, attr)
        assert np.allclose(test_value, value)

    h5file.close()
