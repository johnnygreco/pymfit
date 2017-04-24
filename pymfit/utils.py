from astropy.io import fits

def get_img_center(img_fn, ext=1):
    head = fits.getheader(img_fn, ext=ext)
    X0 = head['NAXIS1']
    Y0 = head['NAXIS2']
    return X0/2, Y0/2    
