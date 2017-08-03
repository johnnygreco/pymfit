from __future__ import division, print_function

import copy
import numpy as np
from .core import SERSIC_PARAMS,AVAILABLE_FUNCS
from .configs import DEFAULT_SERSIC
from .sersic import Sersic

__all__ = ['MultiComponentModel', 'MultiComponentResults']

# Pair imfit model names with model classes
CLASS_NAMES = { 'Sersic':Sersic }

class MultiComponentModel ( object ):
    """
    Container class to hold the information needed to execute and reconstruct a fit
    with multiple objects and components.
    
    """
    def __init__ ( self ):
        self.config_tree = {}
        self.nobjects = 0
        self.fit = False
        
    def add_object ( self, gal_pos='center', img_shape=None, delta_pos=50.):
        '''
        Add object (i.e. position) to the fit. 
        '''
        if gal_pos == 'center':
            assert img_shape is not None, 'must give shape!'
            if type(img_shape) == str:
                img_shape = fits.getdata(img_shape).shape
            gal_pos = img_shape[1]/2, img_shape[0]/2


        x0 = [gal_pos[0], gal_pos[0]-delta_pos, gal_pos[0]+delta_pos]
        y0 = [gal_pos[1], gal_pos[1]-delta_pos, gal_pos[1]+delta_pos]
        mc = ModelContainer ( self.nobjects, [x0,y0] )
        
        self.config_tree [ self.nobjects ] = mc
        self.nobjects += 1
        
    def add_component ( self, objnumber, funcname, init_params={}):
        '''
        Add a component to an extant object

        Parameters
        ----------
        objnumber : int
            Object ID number (as assigned during MultiComponentModel.add_object)
        funcname : string
            Name of the functional form, as defined by imfit
        init_params : dict 
            Non-default initial parameters for the component
        '''
        
        if funcname not in AVAILABLE_FUNCS:
            raise NotImplementedError ( '{0} not implemented in pymfit.'.format(funcname) )

        imfit_config = copy.deepcopy ( globals()['DEFAULT_{0}'.format(funcname.upper())] )
        for k,v in init_params.items():
            imfit_config[k] = v  

        assert objnumber < self.nobjects, "No object #{0} in model.".format(objnumber)
        self.config_tree [ objnumber ].add_component ( funcname, imfit_config )



class MultiComponentResults ( MultiComponentModel ):
    def __init__ ( self ):
        super ( MultiComponentResults, self).__init__ ()
        self.fit = True
        self._reduced_chisq = None

    def add_object ( self, x0, x0_err, y0, y0_err ):
        rs = ResultContainer ( self.nobjects, x0, x0_err, y0, y0_err )
        self.config_tree [ self.nobjects ] = rs
        self.nobjects += 1

    def add_function ( self, objnumber, funcname ):
        self.config_tree [ objnumber ].add_function ( funcname )

    def add_parameter ( self, objnumber, component_number, name, param, param_err ):
        self.config_tree[objnumber].add_parameter ( name, param, param_err, component_number )
        
    @property
    def reduced_chisq ( self ):
        assert self._reduced_chisq is not None, "No reduced chi^2 recorded!"
        return self._reduced_chisq

    @reduced_chisq.setter
    def reduced_chisq ( self, value ):
        self._reduced_chisq = value
        
    def array ( self, shape, logscale=False ):
        '''
        Get 2D array of multicomponent model
        '''
        ys, xs = np.indices ( shape )
        ovlmodel = np.zeros ( shape )
        for oid in range(self.nobjects):
            cobj = self.config_tree[oid]

            for cid in range(cobj.ncomponents):
                funcname, params = cobj[cid]
                model = CLASS_NAMES[funcname] ( params )
                ovlmodel += model.array ( shape )

        return ovlmodel
            
class ModelContainer ( object ):
    """
    Container class to hold information about an individual object in the model.
    """
    def __init__ ( self, object_number, object_position ):
        self.object_number = object_number
        self.position = dict ( zip (['X0','Y0'], object_position ) )
        self.ncomponents = 0
        self.component_nests = {}

    def __getitem__ ( self, key ):
        return self.component_nests[key]

    def add_component ( self, funcname, imfit_config ):
        '''
        Add a new component to the model.
        '''
        self.component_nests[self.ncomponents] = ( funcname, imfit_config )
        self.ncomponents += 1

class ResultContainer ( object ):
    """
    Container class to hold information about an individual object from an imfit output file
    """
    def __init__ ( self, object_number, X0, X0_err, Y0, Y0_err ):
        self.object_number = object_number
        self.X0 = X0
        self.X0_err = X0
        self.Y0 = Y0
        self.Y0_err = Y0
        self.ncomponents = 0
        self.component_nests = {}

    def __getitem__ ( self, key ):
        return self.component_nests[key]

    def add_function ( self, funcname ):
        params = { 'X0': self.X0,
                   'X0_err': self.X0_err,
                   'Y0': self.Y0,
                   'Y0_err': self.Y0_err }
        self.component_nests[self.ncomponents] = ( funcname, params )
        self.ncomponents += 1

    def add_parameter ( self, name, param, param_err, component_number=None ):
        if component_number is None:
            component_number = self.ncomponents

        self.component_nests[component_number][1][name] = param
        self.component_nests[component_number][1][name+'_err'] = param_err
