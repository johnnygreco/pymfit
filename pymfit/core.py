"""
Some tools for running imfit and reading its outputs.
"""
from __future__ import division, print_function

import os

__all__ = ['SERSIC_PARAMS', 'run', 'write_config', 'read_results']


# do not change parameter order
SERSIC_PARAMS = ['X0', 'Y0', 'PA', 'ell', 'n', 'I_e', 'r_e']


def run(img_fn, config_fn, mask_fn=None, var_fn=None, save_model=False,  
        save_res=False, out_fn='bestfit_imfit_params.dat', config=None, 
        psf_fn=None, poisson_mlr=False, quiet=False, cashstat=False,
        mcmc=False, mcmc_prefix='mcmc_out', bootstrap=0, bootstrap_fn=None,
        options=''):
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
        Variance map fits file name. 
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
    options: string, optional
        Additional command-line options. Can be anything imfit takes.
        e.g., '--max-threads 5 --seed 341 --quiet'
        
    Returns
    -------
    results : dict
        Imfit's best-fit parameters and the reduced chi-square
        value of the fit. 
    """

    import subprocess
    cmd = 'imfit-mcmc ' if mcmc else 'imfit ' 
    cmd += "'"+img_fn+"' -c "+config_fn+" "
    if mask_fn is not None:
        cmd += "--mask '"+mask_fn+"' "
    if var_fn is not None:
        cmd += "--noise '"+var_fn+"' --errors-are-variances "
    if psf_fn is not None:
        cmd += "--psf '"+psf_fn+"' "
    if poisson_mlr:
        cmd += '--poisson-mlr '
    if quiet:
        cmd += '--quiet '
    if cashstat:
        cmd += '--cashstat '
    if bootstrap:
        cmd += '--bootstrap {} '.format(bootstrap)
        if bootstrap_fn:
            cmd += '--save-bootstrap {} '.format(bootstrap_fn)

    cmd += options+' '
    if save_model:
        save_fn = img_fn[:-8] if img_fn[-1]==']' else img_fn[:-5]
        save_fn += '_model.fits'
        cmd += '--save-model '+save_fn+' '
    if save_res:
        res_fn = img_fn[:-8] if img_fn[-1]==']' else img_fn[:-5]
        res_fn += '_res.fits'
        cmd += '--save-residual '+res_fn+' '
    if not mcmc:
        cmd += '--save-params '+out_fn
    if config is not None:
        write_config(config_fn, config)
    subprocess.call(cmd, shell=True)
    results = read_results(out_fn)
    return results


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

    function = 'Sersic'
    file = open(fn, 'w')
    for p in SERSIC_PARAMS:
        val = param_dict[p]
        if type(val) is list:
            if len(val)==1:
                val, limit = val[0], ''
            elif len(val)==2:
                val, limit = val
            elif len(val)==3:
                val, lo, hi = val
                limit = str(lo)+','+str(hi)
            else:
                os.remove(fn)
                raise Exception('Invalid parameter definition.')
        else:
            limit = ''
        print(p, val, limit, file=file)
        if p=='Y0':
            print('FUNCTION Sersic', file=file)
    file.close()


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
    comments = [l for l in lines if l[0]=='#']
    params = [l for l in lines if l[0]!='#' if l[:2]!='\n' if l[0]!='F']

    results = {}

    reduced_chisq = [c for c in comments if 
                     c.split()[1]=='Reduced'][0].split()[-1]
    if reduced_chisq != 'none':
        results['reduced_chisq'] =float(reduced_chisq)

    if model=='sersic':
        for i in range(7):
            results[SERSIC_PARAMS[i]] = float(params[i].split()[1])
            if len(params[i].split())==4:
                results[SERSIC_PARAMS[i]+'_err'] = float(params[i].split()[4])

    return results
