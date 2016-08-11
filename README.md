# IP: Application Development

These scripts convert (all?) csv files of a given directory to GeoTIFF
using GDAL's Grid function. Prerequisite is, that there are three columns
containing longitude, latitude and data value.



# Prerequisites
Python 2.7 and GDAL (including their python bindings) are needed to run
these scripts. I recommend using the <Anaconda>-Python distribution, as
they have a very nice way of managing multiple python environments. Every
other Python should do as well, as long as GDAL and it's Python libraries
(tested on version 2.1.0) are installed correctly.

To setup an environment with the name "ip-app-dev" using Python 2.7 and
installing the GDAL libraries use the following on the commandline.

`conda create -n ip-app-dev python=2.7 gdal=2.1.0`
`source activate ip-app-dev`

Now all environments should be set correctly and you can run the scripts
from the commandline.

`pip install -e git+https://github.com/geopython/pywps.git@master#egg=pywps`

IP application development
