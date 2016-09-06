"""
Creates images from CSV input using gdal.Grid()
"""

import argparse
import fnmatch
import logging
import os
from datetime import datetime, timedelta
from os.path import isfile, join, isdir

from utils import gdalUtils

logging.basicConfig(level=logging.INFO)

VRT_TEMPLATE = """
<OGRVRTDataSource>
    <OGRVRTLayer name="$NAME$">
        <SrcDataSource>$PATH$/$FILENAME$</SrcDataSource>
        <GeometryType>wkbPoint</GeometryType>
        <LayerSRS>EPSG:31258</LayerSRS>
        <GeometryField separator=";" encoding="PointFromColumns" x="field_2" y="field_1" z="field_3"/>
    </OGRVRTLayer>
</OGRVRTDataSource>
"""

# setup argument parser
argParser = argparse.ArgumentParser()
argParser.add_argument("input_directory", help="directory that contains the input files.")
argParser.add_argument("output_directory", help="directory the output GeoTIFFs are written to.")
argParser.add_argument("--vrt_template", help="File that contains a template VRT to use when converting the CSV.",
                       default=None)
argParser.add_argument("--fill_interval",
                       help="If set to other than 0 this will create NODATA geotiffs for missing input files.",
                       type=int, default=0)
argParser.add_argument("--name_format", help="Format of input file names. ONLY USED TO GET TIMESTAMP.",
                       default="inca_sbgl_%Y%m%d-%H%M+000.csv")

# get arguments and fill variables
args = argParser.parse_args()
inputDirectory = os.path.abspath(args.input_directory)
outputDirectory = os.path.abspath(args.output_directory)
filenameFormat = args.name_format

interval = None
if args.fill_interval != 0:
    interval = timedelta(minutes=args.fill_interval)

vrtTemplate = VRT_TEMPLATE
if args.vrt_template:
    if isfile(args.vrt_template):
        with open(args.vrt_template, "r") as vrtFile:
            vrtTemplate = vrtFile.read()
    else:
        logging.warn("'{}' is not a file, using default VRT template".format(args.vrt_template))

# this needs to be set, in order to find the gcs.csv/pcs.csv for the EPSG codes
if not os.environ.has_key("GDAL_DATA"):
    logging.warn("Environment GDAL_DATA not set. If you get an error similar to "
                 "'Unable to open EPSG support file gcs.csv.' try setting the"
                 "environment.")
    os.environ["GDAL_DATA"] = "/Users/steffen/anaconda/envs/ip-app-dev/share/gdal"

# get all CSV files in inputDirectory
csvFiles = [f for f in os.listdir(inputDirectory)
            if isfile(join(inputDirectory, f)) and fnmatch.fnmatch(join(inputDirectory, f), "*.csv")]

if not isdir(outputDirectory):
    logging.info("Creating target directory {}".format(outputDirectory))
    os.mkdir(outputDirectory)

lastDatetime = None
for csvFile in csvFiles:
    logging.info("current file: {}".format(csvFile))

    # fill up intervals if requested
    if interval:
        nextDatetime = datetime.strptime(csvFile, filenameFormat)

        if lastDatetime:
            logging.info("Last timestamp was {}. Checking for gaps to {}".format(lastDatetime, nextDatetime))
            while (lastDatetime + interval < nextDatetime):
                lastDatetime = lastDatetime + interval
                outputFilename = datetime.strftime(lastDatetime, filenameFormat) + ".tif"
                logging.warn("Missing {} - adding GeoTIFF {} containing NO_DATA ".format(lastDatetime, outputFilename))
                gdalUtils.createNoDataTif(inputFile=outputDirectory + "/" + csvFiles[0] + ".tif",
                                          outputFile=outputDirectory + "/" + outputFilename)

        lastDatetime = nextDatetime

    # convert CSV
    gdalUtils.convertCsv2Tif(inputPath=inputDirectory,
                             outputPath=outputDirectory,
                             inputFilename=csvFile,
                             vrtTemplateString=vrtTemplate)
