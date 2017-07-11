from astropy.io import fits

def get_img_center(img, ext=1):
    if type(img)==str:
        head = fits.getheader(img, ext=ext)
        X0 = head['NAXIS1']
        Y0 = head['NAXIS2']
    else:
        Y0, X0 = img.shape
    return X0/2, Y0/2    
