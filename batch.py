import os

def batch_launch(reason='', tags=[], **kwargs):
    cmd = 'qsub -cwd -o {0} -e {0} launcher'.format('.qsub')
    for k, v in kwargs.iteritems():
        cmd += ' {0}={1}'.format(k, v)
    cmd += ' --reason="{0}"'.format(reason)
    for t in tags:
        cmd += ' --tag={0}'.format(t)
    os.system(cmd)









