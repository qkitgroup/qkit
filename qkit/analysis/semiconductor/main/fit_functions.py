import numpy as np


def sech(x, a, b, c):
    """Returns the hyperbolic secant of the given x values"""
    return a / np.cosh((x - c) / b)

def multi_sech(x, *params):
    """Returns the sum of multiple hyperbolic secants
    according to the number of given parameters"""
    y = np.zeros_like(x)
    for i in range(0, len(params), 3):
        a = params[i]
        b = params[i + 1]
        c = params[i + 2]
        y = y + sech(x, a, b, c)
    return y

def gauss_function(x, a, x0, sigma):
    """prefactor "a" takes non-normalized data into account. 
    """
    return a * np.exp(-1 * ((x-x0)**2/(2*sigma**2)))

def linear(x, a, b):
    return a * x + b

def bilinear2(x, a, b, c, switch_point):
    x = np.array(x)
    part1 = a * x[x <= switch_point] + b
    part2 = c * x[x > switch_point] + (a - c) * switch_point + b
    return np.concatenate((part1, part2))