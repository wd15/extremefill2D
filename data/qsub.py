import tempfile
import os
import shutil
import subprocess

from extremefill.simulation2D import Simulation2D

def run(CFL=0.4, h5file=None, Nx=300):
    simulation = Simulation2D()
    (f, datafile) = tempfile.mkstemp(suffix='.h5')

    simulation.run(view=False,
                   totalSteps=100000,
                   sweeps=30,
                   dt=0.01,
                   tol=1e-1,
                   Nx=Nx,
                   CFL=CFL,
                   PRINT=True,
                   areaRatio=2 * 0.093,
                   dtMax=100.,
                   dataFile=datafile,
                   totalTime=5000.,
                   Nnarrow=100000000000,
                   data_frequency=10)

    if h5file is None:
        h5file = os.path.split(datafile)[1]
    
    shutil.move(datafile, h5file)

def write_qsubfile(pystring, qsubfile):
    f = open(qsubfile, 'w')
    commands = ['#!/bin/bash\n',
                'source ~/.bashrc\n',
                'workon fipy\n',
                'python -c "{pystring}"\n'.format(pystring=pystring)]

    f.writelines(commands)
    f.close()

def submit():

    CFLfrac = 400
    for Nx in (150, 300, 600, 1200):
        suffix = 'CFL{CFLfrac}Nx{Nx}'.format(CFLfrac=CFLfrac, Nx=Nx)
        qsubfile = suffix + '.qsub'
        h5file = suffix + '.h5'

        pystring = """
import qsub;
qsub.run(CFL={CFL},
         h5file='{h5file}',
         Nx={Nx})""".format(CFL=CFLfrac / 1000., h5file=h5file, Nx=Nx)

        write_qsubfile(pystring, qsubfile)
        efile = '$JOB_NAME.e$JOB_ID'
        ofile = '$JOB_NAME.o$JOB_ID'
        subprocess.call(['qsub', '-cwd', '-e', efile, '-o', ofile, qsubfile])

if __name__ == '__main__':
    submit()

                    
                    

