from __future__ import division, print_function

import copy
from .core import SERSIC_PARAMS,AVAILABLE_FUNCS
from .configs import DEFAULT_SERSIC

__all__ = ['MultiComponentModel']

class MultiComponentModel ( object ):
    """
    Container class to hold the information needed to execute and reconstruct a fit
    with multiple objects and components.
    
    """
    def __init__ ( self ):
        self.config_tree = {}
        self.nobjects = 0

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

        imfit_config = copy.copy ( globals()['DEFAULT_{0}'.format(funcname.upper())] )
        for k,v in init_params.items():
            imfit_config[k] = v  

        assert objnumber < self.nobjects, "No object #{0} in model.".format(objnumber)
        self.config_tree [ objnumber ].add_component ( funcname, imfit_config )
        

            
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

