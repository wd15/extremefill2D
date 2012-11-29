import tempfile
import os
import shutil
import subprocess

from extremefill.simulation2D import Simulation2D

def run(CFL=0.4, h5file=None):
    simulation = Simulation2D()
    (f, datafile) = tempfile.mkstemp(suffix='.h5')

    simulation.run(view=False, totalSteps=5, sweeps=30, dt=0.01, tol=1e-1, Nx=300, CFL=CFL, PRINT=True, areaRatio=2 * 0.093, dtMax=100., dataFile=datafile, totalTime=5000., Nnarrow=100000000000)

    if h5file is None:
        h5file = os.path.split(datafile)[1]
    
    shutil.move(datafile, h5file)

def create_qsubfile(pystring):
    f, filename = tempfile.mkstemp(suffix='', dir='.', text=True)
    f = os.fdopen(f, 'w')
    commands = ['#!/bin/bash\n',
                'source ~/.bashrc\n',
                'workon fipy\n',
                'python -c "{pystring}"\n'.format(pystring=pystring)]

    f.writelines(commands)
    f.close()
    return filename

def submit():
#    for CFL in (0.4, 0.2, 0.1, 0.05, 0.025):
    for CFLfrac in (400,):
        h5file = "'data-CFL-{CFLfrac}.h5'".format(CFLfrac=CFLfrac)
        pystring = '''
import qsub;
qsub.run(CFL={CFL},
         h5file={h5file})'''.format(CFL=CFLfrac / 1000., h5file=h5file)
        qsubfile = create_qsubfile(pystring)
        subprocess.call(['qsub', '-cwd', qsubfile])
#        os.remove(qsubfile)

if __name__ == '__main__':
    submit()

                    
                    
