"""
Model and Param classes for defining arbitrary
imfit models.
"""

from collections import OrderedDict

__all__ = ['default_params', 'param_names', 'Param',
           'ModelComponent', 'Model']

###########################
# Default model parameters
###########################

DEFAULT_SERSIC = OrderedDict([
    ('PA', [20., 0., 360]),
    ('ell', [0.2, 0., 0.99]),
    ('n', [1.0, 0.01, 5]),
    ('I_e', [0.05, 0., 1000]),
    ('r_e', [20., 0., 5000])
])

DEFAULT_SERSIC_GENELLIPSE = OrderedDict([
    ('PA', [20., 0., 360]),
    ('ell', [0.2, 0., 0.99]),
    ('c0', [0.0, -0.2, 0.2]),
    ('n', [1.0, 0.01, 5]),
    ('I_e', [0.05, 0., 1000]),
    ('r_e', [20., 0., 5000])
])

DEFAULT_EXP = OrderedDict([
    ('PA', [20., 0., 360]),
    ('ell', [0.2, 0., 0.99]),
    ('I_0', [0.05, 0., 1000]),
    ('h', [20., 0., 5000])
])

DEFAULT_BROKENEXP = OrderedDict([
    ('PA', [20., 0., 360]),
    ('ell', [0.2, 0., 0.99]),
    ('I_0', [0.05, 0., 1000]),
    ('h1', [4., 0., 5000]),
    ('h2', [8., 0., 5000]),
    ('r_break', [20., 0., 5000]),
    ('alpha', [1., 0.5, 5.])
])

DEFAULT_EDGEDISK = OrderedDict([
    ('PA', [20., 0., 360]),
    ('L_0', [0.05, 0., 1000]),
    ('h', [20., 0., 5000]),
    ('n', [2., 1., 100]),
    ('z_0', [2., 1., 100]),
])

DEFAULT_GAUSS = OrderedDict([
    ('PA', [20., 0., 360]),
    ('ell', [0.2, 0., 0.99]),
    ('I_0', [1.0, 0.01, 5]),
    ('sigma', [0.1, 0.01, 1])
])

DEFAULT_RING = OrderedDict([
    ('PA', [20., 0., 360]),
    ('ell', [0.2, 0., 0.99]),
    ('A', [1.0, 0.01, 5]),
    ('R_ring', [2.0, 0.1, 10]),
    ('sigma_r', [1.0, 0.2, 5.0])
])

DEFAULT_FLATSKY = OrderedDict([
    ('I_sky', [0., -5, 5])
])

DEFAULT_MOFFAT = OrderedDict([
    ('PA', [20., 0., 360]),
    ('ell', [0.2, 0., 0.99]),
    ('I_0', [1.0, 0.01, 5]),
    ('fwhm', [0.2, 0.01, 10]),
    ('beta', [2.0, 0.1, 5])
])

DEFAULT_MODIFIEDKING = OrderedDict([
    ('PA', [20., 0., 360]),
    ('ell', [0.2, 0., 0.99]),
    ('I_0', [1.0, 0.01, 5]),
    ('r_c', [0.2, 0.01, 10]),
    ('r_t', [2.0, 0.1, 20]),
    ('alpha', [2.0, 1.0, 5.0])
])

DEFAULT_POINTSOURCE = OrderedDict([
    ('I_tot', [1.0, 0.01, 5])
])

SERSIC_PARAMS = ['PA', 'ell', 'n', 'I_e', 'r_e']
SERSIC_GENELLIPSE_PARAMS = ['PA', 'ell', 'c0', 'n', 'I_e', 'r_e']
GAUSS_PARAMS = ['PA', 'ell', 'I_0', 'sigma']
RING_PARAMS = ['PA', 'ell', 'A', 'R_ring', 'sigma_r']
EXP_PARAMS = ['PA', 'ell', 'I_0', 'h']
BROKENEXP_PARAMS = ['PA', 'ell', 'I_0', 'h1', 'h2', 'r_break', 'alpha']
EDGEDISK_PARAMS = ['PA', 'L_0', 'h', 'n', 'z_0']
FLATSKY_PARAMS = ['I_sky']
MOFFAT_PARAMS = ['PA', 'ell', 'I_0', 'fwhm', 'beta']
MODIFIEDKING_PARAMS = ['PA', 'ell', 'I_0', 'r_c', 'r_t', 'alpha'] 
POINTSOURCE_PARAMS = ['I_tot']


default_params = dict(Sersic=DEFAULT_SERSIC,
                      Sersic_GenEllipse=DEFAULT_SERSIC_GENELLIPSE,
                      Gaussian=DEFAULT_GAUSS,
                      GaussianRing=DEFAULT_RING,
                      FlatSky=DEFAULT_FLATSKY,
                      Exponential=DEFAULT_EXP,
                      BrokenExponential=DEFAULT_BROKENEXP,
                      EdgeOnDisk=DEFAULT_EDGEDISK,
                      Moffat=DEFAULT_MOFFAT,
                      ModifiedKing=DEFAULT_MODIFIEDKING,
                      PointSource=DEFAULT_POINTSOURCE)

param_names = {
    'Sersic': SERSIC_PARAMS,
    'Sersic_GenEllipse': SERSIC_GENELLIPSE_PARAMS,
    'Gaussian': GAUSS_PARAMS,
    'GaussianRing': RING_PARAMS,
    'FlatSky': FLATSKY_PARAMS,
    'Exponential': EXP_PARAMS,
    'EdgeOnDisk': EDGEDISK_PARAMS,
    'BrokenExponential': BROKENEXP_PARAMS,
    'Moffat': MOFFAT_PARAMS,
    'ModifiedKing': MODIFIEDKING_PARAMS,
    'PointSource': POINTSOURCE_PARAMS
}


def _check_kwargs_defaults(kwargs, defaults):
    kw = defaults.copy()
    for k, v in kwargs.items():
        if isinstance(v, list):
            if v[0] is not None:
                kw[k] = v
        elif v is not None:
            kw[k] = v
    return kw


def _parse_limits(lims):
    if isinstance(lims, list):
        if len(lims) == 3:
            val, vmin, vmax = lims
            fixed = False
        elif len(lims) == 2:
            val = lims[0]
            vmin = None
            vmax = None
            fixed = True
    else:
        val = lims
        vmin = None
        vmax = None
        fixed = False
    return val, vmin, vmax, fixed


class Param(object):

    def __init__(self, name, value, vmin=None, vmax=None,
                 fixed=False, relative_limits=False):

        self.name = name
        self._value = None
        self._vmin = None
        self._vmax = None
        self._fixed = fixed
        self.relative_limits = relative_limits
        self.value = value
        if relative_limits and vmin and vmax:
            self.vmin = value - vmin
            self.vmax = value + vmax
        elif (vmin is not None) and (vmax is not None):
            self.vmin = vmin
            self.vmax = vmax

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        if (self.vmin is not None) and (self.vmax is not None):
            assert (val >= self.vmin) and (val <= self.vmax)
        self._value = val

    @property
    def vmin(self):
        return self._vmin

    @vmin.setter
    def vmin(self, val):
        assert val <= self.value
        self._vmin = val

    @property
    def vmax(self):
        return self._vmax

    @vmax.setter
    def vmax(self, val):
        assert val >= self.value
        self._vmax = val

    @property
    def fixed(self):
        return self._fixed

    @fixed.setter
    def fixed(self, val):
        self._fixed = val
        if val:
            self._vmin = None
            self._vmax = None

    @property
    def config_line(self):
        line = '{} {} '.format(self.name, self.value)
        if self.fixed:
            line += 'fixed'
        elif (self.vmin is not None) and (self.vmax is not None):
            line += '{},{}'.format(self.vmin, self.vmax)
        return line

    def set_lim(self, lim):
        self.fixed = False
        if self.relative_limits:
            lim[0] = self.value - lim[0]
            lim[1] = self.value + lim[1]
        self.vmin, self.vmax = lim


class ModelComponent(object):

    def __init__(self, name, params, center=None, **kwargs):
        self.name = name
        self.param_names = param_names[name]

        if params:
            init_pars = _check_kwargs_defaults(params, default_params[name])
        else:
            init_pars = default_params[name]

        self.param_dict = init_pars

        for k, v in init_pars.items():
            val, vmin, vmax, fixed = _parse_limits(v)
            p = Param(k, val, vmin, vmax, fixed, **kwargs)
            setattr(self, k, p)

        if center:
            val, vmin, vmax, fixed = _parse_limits(center[0])
            self.X0 = Param('X0', val, vmin, vmax, fixed, **kwargs)

            val, vmin, vmax, fixed = _parse_limits(center[1])
            self.Y0 = Param('Y0', val, vmin, vmax, fixed, **kwargs)
        else:
            self.X0 = None
            self.Y0 = None

    def set_param(self, name, value, **kwargs):
        mess = '{} not a param of {} function'.format(name, self.name)
        assert name in self.param_names or name in ['X0', 'Y0'], mess
        val = _parse_limits(value)
        p = Param(name, *val, **kwargs)
        setattr(self, name, p)


class Model(object):

    def __init__(self, funcs, params, centers, dcent=30, **kwargs):

        if not isinstance(centers[0], list):
            centers = [centers]
        if not isinstance(funcs, list):
            funcs = [funcs]
        if not isinstance(params, list):
            params = [params]

        self.funcs = funcs
        self.ncomp = len(funcs)

        zipper = zip(funcs, params, centers)
        for num, (func, pars, center) in enumerate(zipper):
            if center:
                if (dcent != 'fixed') and (dcent != 0):
                    min_x = center[0]-dcent if center[0]-dcent > 0  else 1
                    min_y = center[1]-dcent if center[1]-dcent > 0  else 1
                    center[0] = [center[0], min_x, center[0]+dcent]
                    center[1] = [center[1], min_y, center[1]+dcent]
                else:
                    center[0] = [center[0], 'fixed']
                    center[1] = [center[1], 'fixed']
            setattr(self, 'comp_'+str(num+1),
                    ModelComponent(func, pars, center, **kwargs))

    def set_comp_param(self, comp_num, param, value, **kwargs):
        getattr(self, 'comp_'+str(comp_num)).set_param(param, value, **kwargs)
