# -*- coding: utf-8 -*-
# uncertainties_utilities.py provides additional functions uncertainty analysis
# Micha Wildermuth, micha.wildermuth@kit.edu 2023

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import numpy as np
import uncertainties as uncert
from uncertainties import ufloat, unumpy as unp


def sem(a, **kwargs):
    """
    Compute the standard error of the mean along the specified axis.

    Returns the standard error of the mean, that is per definition the standard deviation divided by sqrt(n-1). The
    standard error of the mean is computed for the
    flattened array by default, otherwise over the specified axis.

    Parameters
    ----------
    a : array_like
        Calculate the standard error of the mean of these values.
    axis : None or int or tuple of ints, optional
        Axis or axes along which the standard error of the mean is computed. The default is to compute the standard
        error of the mean of the flattened array.

        If this is a tuple of ints, a standard error of the mean is performed over multiple axes, instead of a single
        axis or all the axes as before.
    dtype : dtype, optional
        Type to use in computing the standard error of the mean. For arrays of integer type the default is float64, for
        arrays of float types it is the same as the array type.
    out : ndarray, optional
        Alternative output array in which to place the result. It must have the same shape as the expected output but
        the type (of the calculated values) will be cast if necessary.
    ddof : int, optional
        Means Delta Degrees of Freedom.  The divisor used in calculations is ``N - ddof``, where ``N`` represents the
        number of elements. By default `ddof` is zero.
    keepdims : bool, optional
        If this is set to True, the axes which are reduced are left in the result as dimensions with size one. With this
        option, the result will broadcast correctly against the input array.

        If the default value is passed, then `keepdims` will not be passed through to the `std` method of subclasses of
        `ndarray`, however any non-default value will be. If the subclass' method does not implement `keepdims` any
        exceptions will be raised.

    Returns
    -------
    sem : ndarray, see dtype parameter above.
        If `out` is None, return a new array containing the standard error of the mean, otherwise return a reference to
        the output array.

    References
    ----------
    https://en.wikipedia.org/wiki/Standard_error
    """
    n = a.shape[kwargs['axis']] if 'axis' in kwargs else np.prod(a.shape)
    return np.std(unp.nominal_values(a), **kwargs) / np.sqrt(n - 1)


def nansem(a, **kwargs):
    """
    Compute the standard error of the mean along the specified axis, while ignoring NaNs.

    Returns the standard error of the mean, that is per definition the standard deviation divided by sqrt(n-1), of the
    non-NaN array elements. The standard error of the mean is computed for the flattened array by default, otherwise
    over the specified axis.

    For all-NaN slices or slices with zero degrees of freedom, NaN is returned and a `RuntimeWarning` is raised.

    Parameters
    ----------
    a : array_like
        Calculate the standard error of the mean of the non-NaN values.
    axis : {int, tuple of int, None}, optional
        Axis or axes along which the standard error of the mean is computed. The default is to compute the standard
        error of the mean of the flattened array.
    dtype : dtype, optional
        Type to use in computing the standard error of the mean. For arrays of integer type the default is float64, for
        arrays of float types it is the same as the array type.
    out : ndarray, optional
        Alternative output array in which to place the result. It must have the same shape as the expected output but
        the type (of the calculated values) will be cast if necessary.
    ddof : int, optional
        Means Delta Degrees of Freedom.  The divisor used in calculations is ``N - ddof``, where ``N`` represents the
        number of non-NaN elements. By default `ddof` is zero.

    keepdims : bool, optional
        If this is set to True, the axes which are reduced are left in the result as dimensions with size one. With this
        option, the result will broadcast correctly against the original `a`.

        If this value is anything but the default it is passed through as-is to the relevant functions of the
        subclasses. If these functions do not have a `keepdims` kwarg, a RuntimeError will be raised.

    Returns
    -------
    sem : ndarray, see dtype parameter above.
        If `out` is None, return a new array containing the standard error of the mean, otherwise return a reference to
        the output array. If ddof is >= the number of non-NaN elements in a slice or the slice contains only NaNs, then
        the result for that slice is NaN.

    References
    ----------
    https://en.wikipedia.org/wiki/Standard_error
    """
    n = a.shape[kwargs['axis']] if 'axis' in kwargs else np.prod(a.shape)
    return np.nanstd(unp.nominal_values(a), **kwargs) / np.sqrt(n - 1)


def umean(a, **kwargs):
    """
    Compute the arithmetic mean and its uncertainties of numbers with uncertainties along the specified axis.

    Returns the average and its uncertainty of the array elements. The average is taken over the flattened array by
    default, otherwise over the specified axis.
    The uncertainty is calculated as standard error of the mean as well as the error propagated uncertainties of the
    input array.
    `float64` intermediate and return values are used for integer inputs.

    Parameters
    ----------
    a : uncertainties.unumpy.ndarray
        Array containing numbers with uncertainties whose mean is desired. If `a` is not an array, a conversion is
        attempted.
    axis : None or int or tuple of ints, optional
        Axis or axes along which the means are computed. The default is to compute the mean of the flattened array.

        If this is a tuple of ints, a mean is performed over multiple axes, instead of a single axis or all the axes as
        before.
    dtype : data-type, optional
        Type to use in computing the mean. For integer inputs, the default is `float64`; for floating point inputs, it
        is the same as the input dtype.
    out : ndarray, optional
        Alternate output array in which to place the result. The default is ``None``; if provided, it must have the same
        shape as the expected output, but the type will be cast if necessary.
        See `ufuncs-output-type` for more details.

    keepdims : bool, optional
        If this is set to True, the axes which are reduced are left in the result as dimensions with size one. With this
        option, the result will broadcast correctly against the input array.

        If the default value is passed, then `keepdims` will not be passed through to the `mean` method of subclasses
        of `ndarray`, however any non-default value will be. If the subclass' method does not implement `keepdims` any
        exceptions will be raised.

    Returns
    -------
    m : uncertainties.unumpy.ndarray
        If `out=None`, returns a new array containing the mean values and its uncertainties, otherwise a reference to
        the output array is returned.
    """
    avg = np.float64(np.squeeze(unp.nominal_values(np.mean(a, **kwargs))))
    std = np.float64(np.squeeze(np.sqrt(unp.std_devs(np.mean(a, **kwargs)) ** 2 +
                                        sem(unp.nominal_values(a), **kwargs) ** 2)))
    if isinstance(avg, np.floating) and isinstance(std, np.floating):
        return ufloat(nominal_value=avg,
                      std_dev=std)
    elif isinstance(avg, np.ndarray) and isinstance(std, np.ndarray):
        return unp.uarray(nominal_values=avg,
                          std_devs=std)
    else:
        raise TypeError('average value and standard deviation do not have compatible dtypes.')


def unanmean(a, **kwargs):
    """
    Compute the arithmetic mean and its uncertainties of numbers with uncertainties along the specified axis, ignoring
    NaNs.

    Returns the average and its uncertainty of the array elements. The average is taken over the flattened array by
    default, otherwise over the specified axis. The uncertainty is calculated as standard error of the mean as well as
    the error propagated uncertainties of the input array.
    `float64` intermediate and return values are used for integer inputs.

    For all-NaN slices, NaN is returned and a `RuntimeWarning` is raised.

    Parameters
    ----------
    a : uncertainties.unumpy.ndarray
        Array containing numbers with uncertainties whose mean is desired. If `a` is not an array, a conversion is
        attempted.
    axis : {int, tuple of int, None}, optional
        Axis or axes along which the means are computed. The default is to compute the mean of the flattened array.
        dtype : data-type, optional
        Type to use in computing the mean. For integer inputs, the default is `float64`; for inexact inputs, it is the
        same as the input dtype.
    out : ndarray, optional
        Alternate output array in which to place the result. The default is ``None``; if provided, it must have the same
        shape as the expected output, but the type will be cast if necessary.
        See `ufuncs-output-type` for more details.

    keepdims : bool, optional
        If this is set to True, the axes which are reduced are left in the result as dimensions with size one. With this
        option, the result will broadcast correctly against the original `a`.
        If the value is anything but the default, then `keepdims` will be passed through to the `mean` or `sum` methods
        of subclasses of `ndarray`. If the subclasses methods does not implement `keepdims` any exceptions will be raised.

    Returns
    -------
    retval : uncertainties.unumpy.ndarray, see dtype parameter above
        If `out=None`, returns a new array containing the mean values and its uncertainties, otherwise a reference to
        the output array is returned. Nan is returned for slices that contain only NaNs.
    """
    avg = np.float64(np.squeeze(unp.nominal_values(np.nanmean(a, **kwargs))))
    std = np.float64(np.squeeze(np.sqrt(unp.std_devs(np.nanmean(a, **kwargs)) ** 2 +
                                        nansem(unp.nominal_values(a), **kwargs) ** 2)))
    if isinstance(avg, np.floating) and isinstance(std, np.floating):
        return ufloat(nominal_value=avg,
                      std_dev=std)
    elif isinstance(avg, np.ndarray) and isinstance(std, np.ndarray):
        return unp.uarray(nominal_values=avg,
                          std_devs=std)
    else:
        raise TypeError('average value and standard deviation do not have compatible dtypes.')


def uaverage(a, axis=None):
    """
    Computes the average and its uncertainties of numbers with uncertainties along the specified axis considering the
    uncertainties of each input value.

    Returns the average and its uncertainty of the array elements weighted by the inverse variance of each input value
    [1]_ that results from the maximum likelihood estimator applied to aGaussian distribution. The average is calculated
    as weighted arithmetic mean [2]_ and the uncertainty is calculated as square root of the weighted sample variance of
    the input array [3]_.
    Both weighted arithmetic mean and weighted sample variance is taken over the flattened array by default, otherwise
    over the specified axis.

    Parameters
    ----------
    a : uncertainties.unumpy.ndarray
        Array containing data with uncertainties to be averaged. If `a` is not an array, a conversion is attempted.
    axis : None or int or tuple of ints, optional
        Axis or axes along which to average `a`.  The default, axis=None, will average over all the elements of the
        input array.
        If axis is negative it counts from the last to the first axis.
        If axis is a tuple of ints, averaging is performed on all the axes specified in the tuple instead of a single
        axis or all the axes as before.

    Returns
    -------
    retval : uncertainties.unumpy.ndarray or uncertainties.ufloat
        Returns the average and its uncertainty along the specified axis weighted by the inverse variance of each input
        value.
        The result dtype follows a general pattern and is uncertainties.ufloat if `axis` is None or else
        uncertainties.unumpy.ndarray.

    References
    ----------
    [1] Guide to the expression of uncertainty in measurement: https://www.bipm.org/utils/common/documents/jcgm/JCGM_100_2008_E.pdf
    [2] Wikipedia page about weighted arithmetic mean: https://en.wikipedia.org/wiki/Weighted_arithmetic_mean
    [3] Wikipedia page about weighted sample variance: https://en.wikipedia.org/wiki/Weighted_arithmetic_mean#Weighted_sample_variance
    """
    w = 1 / unp.std_devs(a) ** 2
    avg = np.sum(w * unp.nominal_values(a), axis=axis, keepdims=True) / np.sum(w, axis=axis, keepdims=True)
    var = np.sum(w * np.subtract(avg, unp.nominal_values(a)) ** 2, axis=axis) / np.sum(w, axis=axis)
    avg = np.float64(np.squeeze(avg))
    if isinstance(avg, np.floating) and isinstance(var, np.floating):
        return ufloat(nominal_value=avg,
                      std_dev=np.sqrt(var))
    elif isinstance(avg, np.ndarray) and isinstance(var, np.ndarray):
        return unp.uarray(nominal_values=avg,
                          std_devs=np.sqrt(var))
    else:
        raise TypeError('average value and variance do not have compatible dtypes.')


def unanaverage(a, axis=None):
    """
    Computes the average and its uncertainties of numbers with uncertainties along the specified axis considering the
    uncertainties of each input value, ignoring NaNs.

    Returns the average and its uncertainty of the array elements weighted by the inverse variance of each input value
    [1]_ that results from the maximum likelihood estimator applied to aGaussian distribution. The average is calculated
    as weighted arithmetic mean [2]_ and the uncertainty is calculated as square root of the weighted sample variance of
    the input array [3]_.
    Both weighted arithmetic mean and weighted sample variance is taken over the flattened array by default, otherwise
    over the specified axis.

    Parameters
    ----------
    a : uncertainties.unumpy.ndarray
        Array containing data with uncertainties to be averaged. If `a` is not an array, a conversion is attempted.
    axis : None or int or tuple of ints, optional
        Axis or axes along which to average `a`.  The default, axis=None, will average over all the elements of the
        input array.
        If axis is negative it counts from the last to the first axis.
        If axis is a tuple of ints, averaging is performed on all the axes specified in the tuple instead of a single
        axis or all the axes as before.

    Returns
    -------
    retval : uncertainties.unumpy.ndarray or uncertainties.ufloat
        Returns the averagea and its uncertainty along the specified axis weighted by the inverse variance of each input
        value.
        The result dtype follows a general pattern and is uncertainties.ufloat if `axis` is None or else

    See Also
    --------
    uaverage : weighted uncertainty average across array propagating NaNs.
    numpy.isnan : Show which elements are NaN.
    numpy.isfinite: Show which elements are not NaN or +/-inf.

    References
    ----------
    [1] Guide to the expression of uncertainty in measurement: https://www.bipm.org/utils/common/documents/jcgm/JCGM_100_2008_E.pdf
    [2] Wikipedia page about weighted arithmetic mean: https://en.wikipedia.org/wiki/Weighted_arithmetic_mean
    [3] Wikipedia page about weighted sample variance: https://en.wikipedia.org/wiki/Weighted_arithmetic_mean#Weighted_sample_variance
    """
    w = 1 / unp.std_devs(a) ** 2
    avg = np.nansum(w * unp.nominal_values(a), axis=axis, keepdims=True) / np.nansum(w, axis=axis, keepdims=True)
    var = np.nansum(w * np.subtract(avg, unp.nominal_values(a)) ** 2, axis=axis) / np.nansum(w, axis=axis)
    avg = np.float64(np.squeeze(avg))
    if isinstance(avg, np.floating) and isinstance(var, np.floating):
        return ufloat(nominal_value=avg,
                      std_dev=np.sqrt(var))
    elif isinstance(avg, np.ndarray) and isinstance(var, np.ndarray):
        return unp.uarray(nominal_values=avg,
                          std_devs=np.sqrt(var))
    else:
        raise TypeError('average value and variance do not have compatible dtypes.')
