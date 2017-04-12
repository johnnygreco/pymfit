""" Use SEP and imfit to perform 2D galaxy fits."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits

try:
    import lsst.afw.image
    LSST_IMPORTED = True
except ImportError:
    LSST_IMPORTED = False

from ..core import run
from ..masking import make_mask
from ..viz import img_mod_res
from ..sersic import Sersic
 
__all__ = ['sersic_fit', 'DEFAULT_PARAMS', 'DEFAULT_MASK']


DEFAULT_PARAMS = {'X0': None , # If None, use center +/- delta_pos pix
                  'Y0': None,  # If None, use center +/- delta_pos pix
                  'PA': [18., 0, 360], 
                  'ell': [0.2, 0, 0.99], 
                  'n': [1.0, 0.01, 5], 
                  'I_e': [0.05, 0.0, 1000],
                  'r_e': [20., 0.0, 5000]}

DEFAULT_MASK = {'thresh': 1.5,
                'backsize': 110, 
                'backffrac': 0.5, 
                'seg_rmin': 100.0, 
                'obj_rmin': 15.0, 
                'grow_sig': 6.0, 
                'mask_thresh': 0.02, 
                'grow_obj': 3.0, 
                'kern_sig': 4.0, 
                'use_hsc_mask': False,
                'sep_extract_kws':{}}


def sersic_fit(img_fn, init_params={}, prefix='fit', clean='both', 
               visualize=False, photo_mask_fn=None, mask_kws={}, 
               delta_pos=50.0, band_label='i', run_kws={}):
    """
    Perform 2D galaxy fit using the hugs.imfit module, 
    which use imfit and SEP. Most of the work in this function is 
    getting all the input parameters ready for imfit (which uses 
    file names) and SEP (which uses numpy arrays).

    Parameters
    ----------
    img_fn : string
        Fits file name of masked image.
    init_params : dict, optional
        Initial imfit parameters that are different from defaults given 
        by DEFAULT_PARAMS.
    prefix : str, optional
        Prefix for all files generate by this function. Can include
        full path if you want files saved in a specific directory. 
    clean : string, optional
        Files to remove after fitting (mask, config, or both).
    visualize : bool, optional
        If True, plot results.
    photo_mask_fn : string
        File name of photometry mask. If None, it will be created
        using sep. 
    mask_kws : dict, optional
        Any parameter for hugs.imfit.make_mask except masked_image
        and out_fn, which are set in this function. Can also
    delta_pos : float, optional
        Uncertainty in position in pixels. Only used if X0=Y0=None, 
        in which case the center of the image is assumed. 
    band_label: str, optional
        Filter label for figure.
    run_kws: dict, optional
        Keywords for pymfit.core.run

    Returns
    -------
    sersic : hugs.imfit.sersic.Sersic 
        Object containing the best-fit sersic model and associated
        derived parameters.
    """

    if LSST_IMPORTED:
        mi = lsst.afw.image.MaskedImageF(img_fn)
        dim = mi.getDimensions()
    else:
        mi = fits.getdata(img_fn)
        dim = mi.shape[1], mi.shape[0]

    ######################################################################
    # Get the parameters for hugs.make_mask 
    ######################################################################

    mask_params = DEFAULT_MASK.copy()
    for k,v in list(mask_kws.items()):
        if k in list(DEFAULT_MASK.keys()):
            mask_params[k] = v
        else:
            raise Exception('Invalid input parameter: '+k)

    ######################################################################
    # Get the coords of the galaxy of interest and set the imfit config.
    ######################################################################

    imfit_config = DEFAULT_PARAMS.copy()
    for k, v in list(init_params.items()):
        imfit_config[k] = v

    if imfit_config['X0'] is None:
        assert imfit_config['Y0'] is None
        gal_pos = dim[0]/2, dim[1]/2
        mask_params['gal_pos'] = gal_pos
        imfit_config['X0'] = [gal_pos[0], gal_pos[0]-delta_pos,
                              gal_pos[0]+delta_pos]
        imfit_config['Y0'] = [gal_pos[1], gal_pos[1]-delta_pos,
                              gal_pos[1]+delta_pos]
    else:
        if type(imfit_config['X0'])==list:
            gal_pos = imfit_config['X0'][0], imfit_config['Y0'][0]
        else:
            gal_pos = imfit_config['X0'], imfit_config['Y0']
        mask_params['gal_pos'] = gal_pos

    ######################################################################
    # Make the photometry mask and save it to a fits file.
    ######################################################################

    if photo_mask_fn is None:
        photo_mask_fn = prefix+'_photo_mask.fits'
        photo_mask = make_mask(mi, out_fn=photo_mask_fn, **mask_params)

    ######################################################################
    # Run imfit. The best-fit params will be saved to out_fn. 
    ######################################################################

    config_fn = prefix+'_config.txt'
    out_fn = prefix+'_bestfit_params.txt'
    var_fn = img_fn+'[3]'
    results = run(
        img_fn+'[1]', config_fn, photo_mask_fn, var_fn,
        out_fn=out_fn, config=imfit_config, **run_kws)

    if visualize:
        img_mod_res(
            img_fn, results, photo_mask_fn, figsize=(16,6), band=band_label)

    if (clean=='mask') or (clean=='both'):
        os.remove(photo_mask_fn)
    if (clean=='config') or (clean=='both'):
        os.remove(config_fn)

    sersic = Sersic(results)

    return sersic
