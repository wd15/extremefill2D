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

def submit(Nx, CFLfrac):
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

    


def submit_multiple_old ():

    CFLfrac = 200
    for Nx in (150, 600, 1200):
        submit(Nx, CFLfrac)

    Nx = 300
    for CFLfrac in (800, 400, 200, 100, 50, 25):
        submit(Nx, CFLfrac)


if __name__ == '__main__':
    submit(2400, 200)
#    submit_multiple()

                    
                    

