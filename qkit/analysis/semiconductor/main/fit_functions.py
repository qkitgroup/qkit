import numpy as np
from numpy.typing import NDArray


def sech(
    x: NDArray[np.float_],
    a: np.float_,
    b: np.float_,
    c: np.float_,
) -> NDArray[np.float_]:
    """Returns the hpyerbolic secant of the given x values"""
    return a / np.cosh(x / b - c)


def multi_sech(x: NDArray[np.float_], *params: np.float_) -> NDArray[np.float_]:
    """Returns the sum of multiple hyperbolic sechants
    according to the number of given parameters"""
    y = np.zeros_like(x)
    for i in range(0, len(params), 3):
        a = params[i]
        b = params[i + 1]
        c = params[i + 2]
        y = y + sech(x, a, b, c)
    return y
