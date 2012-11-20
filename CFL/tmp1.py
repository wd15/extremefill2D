from extremefill.suedo2DSimulation import Suedo2DSimulation
Suedo2DSimulation().run(view=True, totalSteps=1, sweeps=100, dt=1e+20, tol=1e-4, kPlus=25., featureDepth=0.)
raw_input('stopped')
