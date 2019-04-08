"""
Collection of visualization functions for imfit.
"""
from __future__ import division, print_function


import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.visualization import ZScaleInterval
from astropy.convolution import convolve
from .sersic import Sersic
zscale = ZScaleInterval()

__all__ = ['img_mod_res']


def img_mod_res(img_fn, mod_params, mask_fn=None, cmap=plt.cm.gray_r, 
                save_fn=None, show=True, band=None, subplots=None, 
                titles=True, pixscale=0.168, psf_fn=None, zpt=27., 
                fontsize=20, **kwargs):
    """
    Show imfit results: image, model, and residual.
    """


    img = fits.getdata(img_fn)

    if subplots is None:
        subplot_kw = dict(xticks=[], yticks=[])
        fig, axes = plt.subplots(1, 3, subplot_kw=subplot_kw, **kwargs)
        fig.subplots_adjust(wspace=0.08)
    else:
        fig, axes = subplots

    s = Sersic(mod_params, pixscale=pixscale, zpt=zpt)
    model = s.array(img.shape)

    if psf_fn is not None:
        psf = fits.getdata(psf_fn)
        psf /= psf.sum()
        model = convolve(model, psf)

    res = img - model

    vmin, vmax = zscale.get_limits(img)

    param_labels = {}

    if titles:
        titles = ['Original Image', 'Model', 'Residual']
    else:
        titles = ['']*3


    for i, data in enumerate([img, model, res]):
        axes[i].imshow(data, vmin=vmin, vmax=vmax, origin='lower',
                       cmap=cmap, aspect='equal', rasterized=True)
        axes[i].set_title(titles[i], fontsize=fontsize + 4, y=1.01)

    if mask_fn is not None:
        mask = fits.getdata(mask_fn)
        mask = mask.astype(float)
        mask[mask==0.0] = np.nan
        axes[0].imshow(mask, origin='lower', alpha=0.4,
                       vmin=0, vmax=1, cmap='rainbow_r')

    x = 0.05
    y = 0.93
    dy = 0.09
    dx = 0.61
    fs = fontsize
    if band is not None:
        m_tot = r'$m_'+band+' = '+str(round(s.m_tot, 1))+'$'
    else:
        m_tot = r'$m = '+str(round(s.m_tot, 1))+'$'
    r_e = r'$r_\mathrm{eff}='+str(round(s.r_e*pixscale,1))+'^{\prime\prime}$'
    mu_0 = r'$\mu_0='+str(round(s.mu_0,1))+'$'
    mu_e = r'$\mu_e='+str(round(s.mu_e,1))+'$'
    n = r'$n = '+str(round(s.n,2))+'$'

    c = 'b'

    axes[1].text(x, y, m_tot, transform=axes[1].transAxes,
                 fontsize=fs, color=c)
    axes[1].text(x, y-dy, mu_0, transform=axes[1].transAxes,
                 fontsize=fs, color=c)
    axes[1].text(x, y-2*dy, mu_e, transform=axes[1].transAxes,
                 fontsize=fs, color=c)
    axes[1].text(x+dx, y, n, transform=axes[1].transAxes,
                 fontsize=fs, color=c)
    axes[1].text(x+dx, y-dy, r_e, transform=axes[1].transAxes,
                 fontsize=fs, color=c)
    if band is not None:
        axes[1].text(0.9, 0.05, band, color='r', transform=axes[1].transAxes,
                     fontsize=25)
    if 'reduced_chisq' in list(mod_params.keys()):
        chisq = r'$\chi^2_\mathrm{dof} = '+\
                str(round(mod_params['reduced_chisq'],2))+'$'
        axes[1].text(x+dx, y-2*dy, chisq, transform=axes[1].transAxes,
                     fontsize=fs, color=c)

    if show:
        plt.show()

    if save_fn is not None:
        dpi = kwargs.pop('dpi', 200)
        fig.savefig(save_fn, bbox_inches='tight', dpi=dpi)
