"""
Module to launch python jobs with new branch in a temporary location.
"""

import tempfile
import os
from subprocess import Popen, PIPE, call
import shutil

def gitCommand(cmd):    
    p = Popen(['git'] + cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
    p.wait()
    return p.stdout.read()

def gitTopLevel():
    return gitCommand(['rev-parse', '--show-toplevel']).split()[0]

def gitHEAD():
    return gitCommand(['rev-parse', '--abbrev-ref', 'HEAD']).split()[0]

def gitMediaAttributes(mediaext):
    f = open(os.path.join(gitTopLevel(), '.gitattributes'), 'w')
    f.write("*" + mediaext + " filter=media -crlf")
    f.close()

def gitClone(path):
    return gitCommand(['clone', path])

def gitCheckout(branch):
    return gitCommand(['checkout', branch])

def gitBranch(branch):
    return gitCommand(['checkout', '-b', branch])

def gitAdd(f):
    return gitCommand(['add', f])

def gitCommit(message):
    return gitCommand(['commit', '-m', message])

def gitMediaSync():
    return gitCommand(['media', 'sync'])

def gitPushOrigin():
    return gitCommand(['push', 'origin', 'HEAD'])

def gitLaunch(callBack,
              oldbranch=gitHEAD(),
              newbranch=gitHEAD() + '-git-launch-branch',
              subdirectory=os.path.relpath(os.getcwd(),  gitTopLevel()),
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

    repositoryPath=gitTopLevel()
    tempdir = tempfile.mkdtemp()
    print tempdir
    os.chdir(tempdir)
    gitClone(repositoryPath)
    os.chdir(os.path.split(repositoryPath)[1])
    gitCheckout(oldbranch)
    gitBranch(newbranch)
    os.chdir(subdirectory)
    
    callbackfile = 'callback.py'
    f = open(callbackfile, 'w')
    argList = ['{k}={v}'.format(k=k, v=v) for k, v in kwargs.iteritems()]
    s = 'from ' + callBack.func_globals['__name__'] + ' import ' + callBack.func_name + '\n'
    s += callBack.func_name + '(' +  ', '.join(argList) + ')'
    f.write(s)
    f.close()

    datafile = callBack(**kwargs)

    if datafile is not None:
        gitMediaAttributes(os.path.splitext(datafile)[1])
        gitAdd(datafile)
        gitAdd(callbackfile)
        gitCommit("Adding " + datafile + " data file for " + newbranch + ".")
        gitMediaSync()
        gitPushOrigin()

    os.chdir(tempdir)
    os.chdir('..')
    shutil.rmtree(tempdir)
    
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
from pygit import gitLaunch
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
