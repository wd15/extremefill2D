import numpy as np
    
class Simulation1DODE(object):
    def run(self,
            delta = 100e-6, ## m
            deltaRef = 50e-6, ## m
            faradaysConstant = 9.6485e4, ## C / mol = J / V / mol
            gasConstant = 8.314, ## J / K / mol
            temperature = 298., ## K
            alpha = 0.4,
            appliedVoltage = -0.275,  ## V
            i0 = 40., ## A / m**2 
            capacitance = 0.3, ## F / m**2 = A s / V / m**2  
            kappa = 15.26): ## S / m = A / V / m):

        Fbar = faradaysConstant / gasConstant / temperature ## 1 / V
    
        def iF(potential):
            return i0 * (np.exp(alpha * Fbar * potential) - np.exp(-(2 - alpha) * Fbar * potential))

        def iFderivative(potential):
            return i0 * (alpha * Fbar * np.exp(alpha * Fbar * potential) \
                   + (2 - alpha) * Fbar * np.exp(-(2 - alpha) * Fbar * potential))

        def RHS(t, y):
            potential = y[0]
            return np.array((-iF(potential) / capacitance  - kappa * (potential + appliedVoltage) / deltaRef / capacitance,))

        def jacobian(t, y):
            potential = y[0]
            return np.array((-iFderivative(potential) / capacitance  - kappa / deltaRef / capacitance,))

        from scipy.integrate import ode
        integrator = ode(RHS, jacobian).set_integrator('vode', method='bdf', with_jacobian=True)
        initialValue = -appliedVoltage # + (delta - deltaRef) / deltaRef * appliedVoltage
        integrator.set_initial_value((initialValue,), 0.)

        totalSteps = 200
        dt = .5e-7
        times = np.zeros(totalSteps)
        potentialSciPy = np.zeros(totalSteps)
        step = 0

        while integrator.successful() and step < totalSteps:
            integrator.integrate(integrator.t + dt)
            times[step] = integrator.t
            potential =  integrator.y[0]
            potentialSciPy[step] = -potential
            step += 1

        return np.array(times), np.array(potentialSciPy) 
