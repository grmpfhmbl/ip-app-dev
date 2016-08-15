import argparse
import fnmatch
import logging
import os
from datetime import timedelta, datetime
from os.path import isfile, join, isdir
import csv

from utils import gdalUtils

logging.basicConfig(level=logging.INFO)

# setup argument parser
argParser = argparse.ArgumentParser()
argParser.add_argument("input_directory", help="directory that contains the series GeoTIFFs.")
argParser.add_argument("output_file", help="output file to be written")
argParser.add_argument("latitude", help="Latitude", type=float)
argParser.add_argument("longitude", help="Longitude", type=float)
argParser.add_argument("--name_format", help="Format of input file names. ONLY USED TO GET TIMESTAMP.",
                       default="inca_sbgl_%Y%m%d-%H%M+000.csv.tif")
argParser.add_argument("--no_data_as_none", help="Switch to decide how to treat NODATA values. Either empty cell (true)"
                                                 "or the NODATA value from the band (false)", action="store_true")

# get arguments and fill variables
args = argParser.parse_args()
inputDirectory = os.path.abspath(args.input_directory)
outputFilename = os.path.abspath(args.output_file)
filenameFormat = args.name_format
latitude = args.latitude
longitude = args.longitude
noDataAsNone = args.no_data_as_none

logging.info(args.no_data_as_none)
logging.info(noDataAsNone)

# get all tif files in inputDirectory
tifFiles = [f for f in os.listdir(inputDirectory)
            if isfile(join(inputDirectory, f)) and fnmatch.fnmatch(join(inputDirectory, f), "*.tif")]

outputDirectory = os.path.dirname(outputFilename)
if not isdir(outputDirectory):
    logging.info("Creating target directory {}".format(outputDirectory))
    os.mkdir(outputDirectory)

# dictionary to store timeseries values
values = dict()
for tifFile in tifFiles:
    logging.info("current file: {}".format(tifFile))
    currentDatetime = datetime.strptime(tifFile, filenameFormat)

    # get value from raster
    v = gdalUtils.getValueForCoordinate(inputDirectory + "/" + tifFile, lat=latitude, lon=longitude, noDataAsNone=noDataAsNone)
    logging.info("Value at {}: {}".format(currentDatetime, v))
    values[currentDatetime] = v

logging.info("Opening '{}' for writing. Truncating if it already exists.".format(outputFilename))
with open(outputFilename, 'w+') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["timestamp", "value at ({},{})".format(longitude, latitude)])
    for k, v in values.items():
       writer.writerow([k, v])