"""
Some tools for running imfit and reading its outputs.
"""
from __future__ import division, print_function

import os
import subprocess

__all__ = ['SERSIC_PARAMS', 'run', 'write_config', 'write_multicomponentconfig', 'read_results',
           'read_multicomponentresults' ]

# add list of imfit functions that are available
AVAILABLE_FUNCS = ['Sersic']


# do not change parameter order
SERSIC_PARAMS = ['X0', 'Y0', 'PA', 'ell', 'n', 'I_e', 'r_e']


def run(img_fn, config_fn, mask_fn=None, var_fn=None, sigma=False, 
        save_model=False, save_res=False, out_fn='bestfit_imfit_params.dat', 
        config=None, psf_fn=None, poisson_mlr=False, quiet=False, 
        cashstat=False, mcmc=False, mcmc_prefix='mcmc_out', bootstrap=0, 
        bootstrap_fn=None, mcmc_kws={}, options='', pymfitter=False, 
        weights=False):
    """
    Run imfit.

    Parameters
    ----------
    img_fn : string
        Image fits file name.
    config_fn : string
        The configuration file name.
    mask_fn : string, optional
        Mask fits file with 0 for good pixels and
        >1 for bad pixels.
    var_fn : string, optional
        Noise image fits file name. Either variance or sigma image
    sigma : bool, optional
        If True, treat the noise image as sigma map; otherwise
        treat it as variance image
    save_model : bool, optional
        If True, save the model fits image.
    save_res : bool, optional
        If True, save a residual fits image.
    out_fn : string, optional
        Output file name for best-fit params.
    config : dict, optional
        Configuration parameters to be written to config_fn. If None,
        will assume config_fn already exists.
    psf_fn : str, optional
        PSF fits file.
    poisson_mlr : bool, optional
        If True, use Poisson maximum-likelihood ratio.
    quiet: bool, optional
        If True, supress printing of intermediate fit-statistic
        vaules during the fitting process.
    cashstat: bool, optional
        If True, Use Cash statistic instead of chi^2
    mcmc: bool, optional
        Run imfit-mcmc.
    mcmc_prefix: string, optional
        File prefix for mcmc output.
    bootstrap: int, optional
        Number of iterations for bootstrap resampling.
    bootstrap_fn: str, optional
        Save all bootstrap best-fit parameters to specified file.
    mcmc_kws: dict, optional
        Keyword arguments for imfit-mcmc, which includes nchains,
        max-chain-length, burnin-length, gelman-rubin-limit, uniform-offset,
        and gaussian-offset.
    options: string, optional
        Additional command-line options. Can be anything imfit takes.
        e.g., '--max-threads 5 --seed 341 --quiet'
    pymfitter: bool, optional
        If True, run is being called from a PymFitter instance.
    weights: bool, optional
        If True, treat the noise image as wieght map; otherwise 
        treat it as variance image

    Returns
    -------
    results : dict, if mcmc = False
        Imfit's best-fit parameters and the reduced chi-square
        value of the fit.
    """

    # main imfit of imfit-mcmc call
    cmd = 'imfit-mcmc ' if mcmc else 'imfit '
    print(img_fn, config_fn)
    cmd += "'" + img_fn + "' -c " + config_fn + " "

    # add mask, variance, and/or psf files if given
    if mask_fn is not None:
        cmd += "--mask '" + mask_fn + "' "
    if var_fn is not None:
        if sigma:
            cmd += "--noise '"+var_fn+"'  "
        elif weights:
            cmd += "--noise '"+var_fn+"' --errors-are-weights "
        else:
            cmd += "--noise '"+var_fn+"' --errors-are-variances "
    if psf_fn is not None:
        cmd += "--psf '" + psf_fn + "' "

    # different statistics options
    if poisson_mlr:
        cmd += '--poisson-mlr '
    if cashstat:
        cmd += '--cashstat '

    # limit imfit's output
    if quiet:
        cmd += '--quiet '

    # bootstrap resampling and optional output file
    if bootstrap:
        cmd += '--bootstrap {} '.format(bootstrap)
        if bootstrap_fn:
            cmd += '--save-bootstrap {} '.format(bootstrap_fn)

    # any last imfit options not included above
    cmd += options + ' '

    # save model and/or residual image(s)
    if save_model:
        save_fn = img_fn[:-8] if img_fn[-1] == ']' else img_fn[:-5]
        save_fn += '_model.fits'
        cmd += '--save-model ' + save_fn + ' '
    if save_res:
        res_fn = img_fn[:-8] if img_fn[-1] == ']' else img_fn[:-5]
        res_fn += '_res.fits'
        cmd += '--save-residual ' + res_fn + ' '

    # best-fit param file or mcmc file name prefix
    if not mcmc:
        cmd += '--save-params ' + out_fn
    else:
        cmd += '--output ' + mcmc_prefix + ' '
        # additional mcmc options
        for k, v in mcmc_kws.items():
            cmd += '--{} {} '.format(k, v)

    # create config file if needed
    if config is not None:
        write_config(config_fn, config)

    # run imfit
    subprocess.call(cmd, shell=True)

    if not pymfitter:
        return None if mcmc else read_results(out_fn)

def write_multicomponentconfig(fn, mcmodel):
    '''
    Write imfit config file from a MultiComponentModel object.


    '''
    fileobj = open(fn, 'w')

    for oid in range(mcmodel.nobjects):
        for key in ['X0','Y0']:
            val, lo, hi = mcmodel.config_tree[oid].position[key]
            print(key, val, str(lo)+','+str(hi), file=fileobj)

        for cid in range(mcmodel.config_tree[oid].ncomponents):
            function, component = mcmodel.config_tree[oid][cid]
            print('FUNCTION ' + function, file=fileobj)
            component['X0'] = None
            component['Y0'] = None
            write_component(fileobj, function, component)
        print('\n', file=fileobj)

    fileobj.close()


def write_config(fn, param_dict):
    """
    Write imfit config file. At the moment, I am
    only using Sersic models.

    Parameters
    ----------
    fn : string
        Config file name.
    param_dict : dict
        Imfit initial parameters and optional limits.

    Notes
    -----
    Example format for the parameter dictionary:
    param_dict = {'X0':[330, 300, 360], 'Y0':[308, 280, 340],
                  'PA':18.0, 'ell':[0.2,0,1], 'n':[1.0, 'fixed'],
                  'I_e':15, 'r_e':25}
    Limits are given as a list: [val, val_min, val_max]. If the
    parameter should be fixed, use [val, 'fixed'].
    """
    file = open(fn, 'w')
    file = write_component (file, 'Sersic', param_dict)
    file.close()

def write_component (fileobj, function, param_dict):
    """
    Write one component of a config file.

    Parameters
    ----------
    fn : string
        Config file name.
    param_dict : dict
        Imfit initial parameters and optional limits.

    Notes
    -----
    Example format for the parameter dictionary:
    param_dict = {'X0':[330, 300, 360], 'Y0':[308, 280, 340],
                  'PA':18.0, 'ell':[0.2,0,1], 'n':[1.0, 'fixed'],
                  'I_e':15, 'r_e':25}
    Limits are given as a list: [val, val_min, val_max]. If the
    parameter should be fixed, use [val, 'fixed'].
    """
    fn = fileobj.name

    for p in SERSIC_PARAMS:
        val = param_dict[p]
        if val is None:
            continue
        elif type(val) is list:
            if len(val) == 1:
                val, limit = val[0], ''
            elif len(val) == 2:
                val, limit = val
            elif len(val) == 3:
                val, lo, hi = val
                limit = str(lo)+','+str(hi)
            else:
                os.remove(fn)
                raise Exception('Invalid parameter definition.')
        else:
            limit = ''
        print(p, val, limit, file=fileobj)
        if p == 'Y0':
            print('FUNCTION ' + function, file=fileobj)

    return fileobj

def read_multicomponentresults ( fn ):
    '''
    Read an imfit results file for a multicomponent model.
    '''
    import re
    from .multicomponent import MultiComponentResults

    fileobj = open(fn, 'r')
    lines = fileobj.readlines()
    fileobj.close()
    comments = [l for l in lines if l[0] == '#']

    mcres = MultiComponentResults()

    reduced_chisq = [c for c in comments if
                     c.split()[1] == 'Reduced'][0].split()[-1]
    mcres.reduced_chisq = float(reduced_chisq)

    i = 0
    while i < len(lines):
        if len(lines[i].split()) == 0:
            i += 1
        elif lines[i][0] == '#':
            i += 1
        elif 'X0' in lines[i]:
            _, x0, x0_err = __parse_line(lines[i])
            _, y0, y0_err = __parse_line(lines[i+1])
            funcname = re.findall("(?<=FUNCTION ).*", lines[i+2])[0]
            mcres.add_object(x0, x0_err, y0, y0_err)
            mcres.add_function(mcres.nobjects-1, funcname)
            i += 3
        elif re.match("FUNCTION .*" , lines[i]):
            funcname = re.findall("(?<=FUNCTION ).*", lines[i])[0]
            mcres.add_function(mcres.nobjects-1, funcname)
            i += 1
        else:
            mcres.add_parameter(mcres.nobjects-1,
                                mcres.config_tree[mcres.nobjects-1].ncomponents - 1,
                                *__parse_line(lines[i]))
            i += 1
    return mcres

def __parse_line ( line ):
    data = line.split ()
    if len(data) != 5:
        raise IndexError ("Imfit output not in expected format. Received: \n{0}".format(line))
    name = data[0]
    value = float(data[1])
    error = float(data[-1])
    return name, value, error

def read_results(fn, model='sersic'):
    """
    Read the output results file from imfit.

    Parameters
    ----------
    fn : string
        Imfit file name.
    model : string, optional
        The model used in imfit's fit.

    Returns
    -------
    results : dict
        Imfit best-fit results and reduced chi-square
        value. For Sersic fits, the parameters are
        ['X0', 'Y0', 'PA', 'ell', 'n', 'I_e', 'r_e'].
    """

    file = open(fn, 'r')
    lines = file.readlines()
    file.close()
    comments = [l for l in lines if l[0] == '#']
    params = [l for l in lines if l[0] != '#' if l[:2] != '\n' if l[0] != 'F']

    results = {}

    reduced_chisq = [c for c in comments if
                     c.split()[1] == 'Reduced'][0].split()[-1]
    if reduced_chisq != 'none':
        results['reduced_chisq'] = float(reduced_chisq)

    if model == 'sersic':
        for i in range(7):
            results[SERSIC_PARAMS[i]] = float(params[i].split()[1])
            if len(params[i].split()) == 5:
                results[SERSIC_PARAMS[i]+'_err'] = float(params[i].split()[4])

    return results
