from __future__ import division, print_function

import os
from collections import OrderedDict

import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits

from .core import run

__all__ = ['PymFitter']

class PymFitter(object):

    def __init__(self, model, save_files=False):

        self.model = model
        self.save_files = save_files
        self.results = OrderedDict()
        self.img_fn = None
        self.res_fn = None
        self.model_fn = None
        self.out_fn = None
        self.mask_fn = None
        self.model_arr = None
        self.res_arr = None

    def write_config(self, fn):
        with open(fn, 'w') as file:
            for i in range(self.model.ncomp):
                comp = getattr(self.model, 'comp_'+str(i+1))
                if comp.X0 is not None:
                    print('\n' + comp.X0.config_line, file=file)
                    print(comp.Y0.config_line, file=file)
                print('FUNCTION '+ comp.name, file=file)
                for par in comp.param_names:
                    line = getattr(comp, par).config_line
                    print(line, file=file)

    def print_config(self):
        for i in range(self.model.ncomp):
            comp = getattr(self.model, 'comp_' + str(i+1))
            if comp.X0 is not None:
                print('\n' + comp.X0.config_line)
                print(comp.Y0.config_line)
            print('FUNCTION ' + comp.name)
            for par in comp.param_names:
                line = getattr(comp, par).config_line
                print(line)

    def read_results(self):
        file = open(self.out_fn, 'r')
        lines = file.readlines()
        file.close()
        # comments = [l for l in lines if l[0]=='#']
        params = [l for l in lines if l[0] != '#' if l[:2] != '\n'\
                                   if l[0] != 'F' if l[:2] != 'X0'\
                                   if l[:2] != 'Y0']
        cen_text = [l for l in lines if l[0] != '#'\
                                     if (l[:2] == 'X0' or l[:2] == 'Y0')]

        centers = []

        for i in range(len(cen_text)//2):
            _, x0, _, _, xerr = cen_text[i].split()
            _, y0, _, _, yerr = cen_text[i+1].split()
            pos_list = [float(x0), float(y0), float(xerr), float(yerr)]
            centers.append(pos_list)

        par_num = 0
        cen_num = -1
        # self.results = OrderedDict()
        for i in range(self.model.ncomp):
            comp = getattr(self.model, 'comp_'+str(i+1))
            self.results['comp_'+str(i+1)] = {}
            self.results['comp_'+str(i+1)]['function'] = comp.name
            if comp.X0 is not None:
                cen_num += 1
            self.results['comp_'+str(i+1)]['X0'] = centers[cen_num][0]
            self.results['comp_'+str(i+1)]['Y0'] = centers[cen_num][1]
            self.results['comp_'+str(i+1)]['X0_err'] = centers[cen_num][2]
            self.results['comp_'+str(i+1)]['Y0_err'] = centers[cen_num][3]

            for par in comp.param_names:
                name, val = params[par_num].split()[:2]
                err = params[par_num].split()[-1]
                assert name == par
                self.results['comp_'+str(i+1)].update({par: float(val)})
                self.results['comp_'+str(i+1)].update({par+'_err': float(err)})
                par_num += 1

    def print_results(self):
        for i in range(self.model.ncomp):
            comp = self.results['comp_'+str(i+1)]
            params = getattr(self.model, 'comp_'+str(i+1)).param_names
            print('\nComponent  {}'.format(i+1))
            print('---------------------')
            print('Function   {}'.format(comp['function']))
            print('X0         {}'.format(comp['X0']))
            print('Y0         {}'.format(comp['Y0']))
            for p in params:
                val = comp[p]
                print('{:9}  {:.4f}'.format(p, val))

    def run(self, img_fn, mask_fn=None, var_fn=None, psf_fn=None,
            config_fn='config.txt', out_fn='best-fit.txt', will_viz=False,
            outdir='.', save_model=False, save_residual=False, **run_kws):

        config_fn = os.path.join(outdir, config_fn)
        out_fn = os.path.join(outdir, out_fn)
        self.write_config(fn=config_fn)
        self.out_fn = out_fn
        self.mask_fn = mask_fn

        if will_viz or save_model:
            run_kws['save_model'] = True
        if will_viz or save_residual:
            run_kws['save_res'] = True

        run(img_fn, config_fn, mask_fn=mask_fn, var_fn=var_fn,
            out_fn=out_fn, psf_fn=psf_fn, pymfitter=True, **run_kws)

        self.read_results()

        self.img_fn = img_fn[:-3] if img_fn[-1] == ']' else img_fn
        self.res_fn = img_fn[:-8] if img_fn[-1] == ']' else img_fn[:-5]
        self.res_fn += '_res.fits'
        self.model_fn = img_fn[:-8] if img_fn[-1] == ']' else img_fn[:-5]
        self.model_fn += '_model.fits'

        if will_viz:
            self.model_arr = fits.getdata(self.model_fn)
            self.res_arr = fits.getdata(self.res_fn)
        if not self.save_files:
            os.remove(out_fn)
            os.remove(config_fn)
            if will_viz and not save_model:
                os.remove(self.model_fn)
            if will_viz and not save_residual:
                os.remove(self.res_fn)

    def viz_results(self, subplots=None, show=True, save_fn=None,
                    titles=True, **kwargs):
        from astropy.visualization import ZScaleInterval
        zscale = ZScaleInterval()

        if subplots:
            fig, axes = subplots
        else:
            subplot_kw = dict(xticks=[], yticks=[])
            if 'figsize' not in kwargs.keys():
                kwargs['figsize'] = (16, 6)
            fig, axes = plt.subplots(1, 3, subplot_kw=subplot_kw, **kwargs)
            fig.subplots_adjust(wspace=0.08)

        img = fits.getdata(self.img_fn)
        model = self.model_arr
        res = self.res_arr

        vmin, vmax = zscale.get_limits(img)

        if titles:
            titles = ['Original Image', 'Model', 'Residual']
        else:
            titles = ['']*3

        for i, data in enumerate([img, model, res]):
            axes[i].imshow(data, vmin=vmin, vmax=vmax, origin='lower',
                           cmap='gray_r', aspect='equal', rasterized=True)
            axes[i].set_title(titles[i], fontsize=20, y=1.01)


        if self.mask_fn is not None:
            mask = fits.getdata(self.mask_fn)
            mask = mask.astype(float)
            mask[mask == 0.0] = np.nan
            axes[0].imshow(mask, origin='lower', alpha=0.4,
                           vmin=0, vmax=1, cmap='rainbow_r')

        if show:
            plt.show()

        if save_fn is not None:
            fig.savefig(save_fn, bbox_inches='tight')

        return fig, axes
