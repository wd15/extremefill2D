"""
Module to launch python jobs with new branch in a temporary location.
"""

import tempfile
import os
from subprocess import Popen, PIPE, call
import shutil

def gitCommand(cmd, verbose=False):    
    p = Popen(['git'] + cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
    p.wait()
    out = p.stdout.read()
    if verbose:
        print out
        print p.stderr.read()
    return out

def gitTopLevel(verbose=False):
    return gitCommand(['rev-parse', '--show-toplevel'], verbose=verbose).split()[0]

def gitHEAD():
    return gitCommand(['rev-parse', '--abbrev-ref', 'HEAD']).split()[0]

def gitMediaAttributes(mediaext):
    f = open(os.path.join(gitTopLevel(), '.gitattributes'), 'w')
    f.write("*" + mediaext + " filter=media -crlf")
    f.close()

def gitClone(path, verbose=False):
    return gitCommand(['clone', path], verbose=verbose)

def gitCheckout(branch, verbose=False):
    gitCommand(['checkout', branch], verbose=verbose)

def gitBranch(branch):
    gitCommand(['co', '-b', branch])

def gitAdd(f):
    gitCommand(['add', f])

def gitCommit(message):
    gitCommand(['commit', '-m', message])

def gitMediaSync():
    gitCommand(['media', 'sync'])

def gitPushOrigin():
    gitCommand(['push', '-f', 'origin', 'HEAD'])

def gitFetch(remote='origin'):
    gitCommand(['fetch', remote])

def gitCurrentCommit():
    return gitCommand(['log', '--oneline', '-1', '--abbrev=12', '--format="%h"'])

def gitCloneToTemp(branch=None, repositoryPath=None, verbose=False):
    if repositoryPath is None:
        repositoryPath = gitTopLevel(verbose=verbose)
    tempdir = tempfile.mkdtemp()
    os.chdir(tempdir)
    gitClone(repositoryPath, verbose=verbose)
    os.chdir(os.path.split(repositoryPath)[1])
    if branch is not None:
        gitCheckout(branch, verbose=verbose)
    return tempdir

def cleanTempRepo(tempdir):
    os.chdir(tempdir)
    os.chdir('..')
    shutil.rmtree(tempdir)
    
def gitLaunch(callBack,
              oldbranch=None,
              newbranch=None,
              subdirectory=None,
              **kwargs):
    """
    Creates a temporary directory and checks out a copy of the current
    repository, branches and runs the given python function. If the
    python function returns a data file this is committed as a
    git-media file. This is useful for submitting multiple jobs on a
    cluster and having each job on a separate branch.

    :Parameters:

      - `callBack`: The call back function to call on the new branch
        which returns the datafile to be stored.
      - `oldbranch`: The branch to branch from (git co
        oldbranch). Defaults to the current branch
      - `newbranch`: The new branch to be created (git co -b
        newbranch).
      - `subdirectory`: Subdirectory in repository where data file
        will be stored. Defaults to the current subdirectory.
      - `**kwargs`: Arguments for the call back function.

    """

    if oldbranch is None:
        oldbranch = gitHEAD()

    if newbranch is None:
        newbranch = gitHEAD() + '-git-launch-branch',

    if subdirectory is None:
        subdirectory = os.path.relpath(os.getcwd(),  gitTopLevel())
    
    tempdir = gitCloneToTemp(branch=oldbranch)
    gitBranch(newbranch)
    os.chdir(subdirectory)
    
    callbackfile = 'callback.py'
    f = open(callbackfile, 'w')
    argList = ['{k}={v}'.format(k=k, v=v) for k, v in kwargs.iteritems()]
    s = 'from ' + callBack.func_globals['__name__'] + ' import ' + callBack.func_name + '\n'
    s += 'datafile = ' + callBack.func_name + '(' +  ', '.join(argList) + ')'
    f.write(s)
    f.close()

    import callback
    datafile = callback.datafile

    if datafile is not None:
        gitMediaAttributes(os.path.splitext(datafile)[1])
        gitAdd(datafile)
        gitAdd(callbackfile)
        gitCommit("Adding " + datafile + " data file for " + newbranch + ".")
        gitMediaSync()
        gitPushOrigin()

    cleanTempRepo(tempdir)
    
def getVirtualenv():
    return os.path.split(os.environ.get('VIRTUAL_ENV'))[1]

def write_qsubfile(pystring, qsubfile):
    f = open(qsubfile, 'w')
    commands = ['#!/bin/bash\n',
                'source ~/.bashrc\n',
                'workon {virtualenv}\n'.format(virtualenv=getVirtualenv()),
                'python -c "{pystring}"\n'.format(pystring=pystring)]

    f.writelines(commands)
    f.close()

def qsubmit(callBack,
            oldbranch=gitHEAD(),
            newbranch=gitHEAD() + '-git-launch-branch',
            subdirectory=os.path.relpath(os.getcwd(),  gitTopLevel()),
            **kwargs):

    qsubfile = newbranch + '.qsub'
    kwargstring = ','.join(['{k}={v}'.format(k=k, v=v) for k, v in kwargs.iteritems()])

    pystring = """
from gitqsub import gitLaunch
from {module} import {callBack} as callBack
gitLaunch(callBack, oldbranch='{oldbranch}', newbranch='{newbranch}', subdirectory='{subdirectory}', {kwargstring})
""".format(callBack=callBack.__name__,
           module=callBack.func_globals['__file__'][:-3],
           oldbranch=oldbranch,
           newbranch=newbranch,
           subdirectory=subdirectory,
           kwargstring=kwargstring)

    write_qsubfile(pystring, qsubfile)
    call(['qsub', '-cwd', qsubfile])

if __name__ == '__main__':
    def hello():
        datafile='hello.h5'
        f = open(datafile, 'w')
        f.write('hello')
        f.close()
        return datafile
    
    gitLaunch(hello)
