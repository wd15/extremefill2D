#!/usr/bin/env python
"""
Usage: script.py [<jsonfile>]

"""

__docformat__ = 'restructuredtext'


import shutil
from collections import namedtuple
import json
import os
import tempfile


import tables
from docopt import docopt
from extremefill2D import ExtremeFillSystem


if __name__ == '__main__':
    ## read parameters
    arguments = docopt(__doc__, version='Run script.py')
    jsonfile = arguments['<jsonfile>']
    with open(jsonfile, 'rb') as ff:
        params_dict = json.load(ff)
    params = namedtuple('ParamClass', params_dict.keys())(*params_dict.values())

    datafile = os.path.join(tempfile.gettempdir(), 'data.h5')
    
    system = ExtremeFillSystem(params, datafile)
    system.run()

    if not hasattr(params, 'sumatra_label'):
        sumatra_label = '.'
    else:
        sumatra_label = params.sumatra_label

    finaldir = os.path.join('Data', sumatra_label)

    shutil.move(datafile, finaldir)
