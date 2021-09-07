# astrosaic
Astrophotographic mosaicking tool, based on AstroPy's reproject library.

## Dependencies
 - astropy
 - reproject
 - shapely
 - numpy

## Usage
```bash
python3 mosaic.py image_dir
```
Will generate 3 files: ```red.fits```, ```blu.fits```, ```grn.fits``` and ```rgb.fits```.
