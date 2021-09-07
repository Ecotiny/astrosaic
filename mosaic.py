from astropy.wcs import WCS
import matplotlib.pyplot as plt
from astropy.io import fits
from reproject.mosaicking import find_optimal_celestial_wcs, reproject_and_coadd
from reproject import reproject_interp
import argparse
from pathlib import Path
from datetime import datetime
import numpy as np
from multiprocessing import Pool 

def get_fits(directory):
    outfits = []
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Getting all FITS images")
    for f in directory.iterdir():
        if not f.is_dir():
            outfits.append(fits.open(f))

    return outfits

def get_wcs(all_fits):
    all_wcs = []
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Calculating optimal WCS")
    for f in all_fits:
        hdr = f[0]
        a = hdr.data[0,:,:]
        w = WCS(hdr.header, naxis=2)
        all_wcs.append((a, w))
    wcs_out, shape_out = find_optimal_celestial_wcs(all_wcs,
                                                    frame='galactic')
    return wcs_out, shape_out

def add_single_channel(arr, wcs, shape, fn):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Coadding for {fn}")
    arr_out, arr_ftprnt = reproject_and_coadd(arr,
                                              wcs, shape_out=shape,
                                              reproject_function=reproject_interp,
                                              match_background=True)
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Saving {fn}.fits")
    hdu = fits.PrimaryHDU(arr_out)
    hdu.writeto(f"{fn}.fits", overwrite=True)

    return arr_out

def coadd(all_fits, wcs, shape):
    reds, greens, blues = [], [], []
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Splitting channels")
    for f in all_fits:
        hdr = f[0]
        r, g, b = hdr.data[0,:,:], hdr.data[1,:,:], hdr.data[2,:,:]
        w = WCS(hdr.header, naxis=2)
        reds.append((r, w))
        greens.append((g, w))
        blues.append((b, w))
    
    redargs = (reds, wcs, shape, 'red')
    greenargs = (greens, wcs, shape, 'grn')
    blueargs = (blues, wcs, shape, 'blu')

    with Pool(3) as pool:
        red_p = pool.apply_async(add_single_channel, redargs)
        grn_p = pool.apply_async(add_single_channel, greenargs)
        blu_p = pool.apply_async(add_single_channel, blueargs)

        red_out   = red_p.get(timeout=600) # 10 minutes
        green_out = grn_p.get(timeout=600)
        blue_out  = blu_p.get(timeout=600)

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Compositing to RGB")
    rgb_out = np.dstack((red_out, green_out, blue_out))

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Writing RGB")
    hdu = fits.PrimaryHDU(rgb_out)
    hdu.writeto("rgb.fits", overwrite=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AstroPy image mosaicker")
    parser.add_argument('image_dir', type=str, help="Directory where images are stored, with WCS")
    args = parser.parse_args()
    
    image_dir = Path(args.image_dir)
    # check if exists
    if not image_dir.exists():
        print(f"{image_dir} doesn't exist!")
        exit()

    all_fits = get_fits(image_dir)
    wcs, shape = get_wcs(all_fits)
    
    coadd(all_fits, wcs, shape)

