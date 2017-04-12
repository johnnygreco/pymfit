from __future__ import division, print_function

from astropy.io import fits

__all__ = ['DEFAULT_SERSIC', 'sersic_config']

DEFAULT_SERSIC = {'X0': None ,
                  'Y0': None,  
                  'PA': [20., 0, 360],
                  'ell': [0.2, 0, 0.99],
                  'n': [1.0, 0.01, 5],
                  'I_e': [0.05, 0.0, 1000],
                  'r_e': [20., 0.0, 5000]}

def sersic_config(init_params={}, gal_pos='center', img_shape=None, delta_pos=50.0):
    """
    Create a Sersic model config dictionary for pymfit.run.

    Parameters
    ----------
    init_params: dict, optional
        Initial parameters that are different from DEFAULT_SERSIC. 
        See pymfit.write_config doc string for syntax.
    gal_pos: tuple, optional
        (X0, Y0) position of galaxy. If 'center', will use center of image.
        In this case, must give image shape of file name.
    img_shape: tuple or str, optional
        Image shape or the image file name. 
    delta_pos: float, optional
        The +/- limits for the position. 
    """

    imfit_config = DEFAULT_SERSIC.copy()
    for k, v in list(init_params.items()):
        imfit_config[k] = v
    if 'X0' not in list(init_params.keys()):
        if gal_pos == 'center':
            assert img_shape is not None, 'must give shape!'
            if type(img_shape) == str:
                img_shape = fits.getdata(img_shape).shape
            gal_pos = img_shape[1]/2, img_shape[0]/2
        imfit_config['X0'] = [gal_pos[0], gal_pos[0]-delta_pos,
                              gal_pos[0]+delta_pos]
        imfit_config['Y0'] = [gal_pos[1], gal_pos[1]-delta_pos,
                              gal_pos[1]+delta_pos]
    return imfit_config
