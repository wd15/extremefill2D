from toolz.curried import curry, pipe, last

def latest(treant):
    return pipe(
        treant.glob('*.nc'),
        sorted,
        last,
        lambda leaf: leaf.abspath,
    )

tlam = curry(lambda f, t: f(*t))
