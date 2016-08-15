"""
Utilities for working with GDAL
"""
import logging
import os
import struct

from osgeo import gdal, osr


def convertCsv2Tif(inputPath, outputPath, inputFilename, vrtTemplateString):
    """
    Convert CSV to GeoTIFF using gdal.Grid. Output will be written to <outputPath>/<inputFilename>.tif

    CSV is decribed by the template given as parameter. The following tokens are replaced:
        - $NAME$ by inputFilename without extension
        - $FILENAME$ by inputFilename
        - $PATH$ by the absolute inputPath

    :param inputPath: path to input CSV
    :param outputPath: path to where the output GeoTIFF is written
    :param inputFilename: filename (without path!) of input CSV
    :param vrtTemplateString: template string for VRT file
    """
    # make input and output path absolute in case it is not already
    fullInputPath = os.path.abspath(inputPath)
    fullOutputPath = os.path.abspath(outputPath)

    fullVrtFilename = fullOutputPath + "/" + inputFilename + ".vrt"

    logging.info("Opening '{}' for writing...".format(fullVrtFilename))

    with open(fullVrtFilename, "w+") as currentVrtFile:
        logging.info("writing template to: {}".format(fullVrtFilename))

        currentVrtString = vrtTemplateString \
            .replace("$NAME$", os.path.splitext(inputFilename)[0]) \
            .replace("$FILENAME$", inputFilename) \
            .replace("$PATH$", fullInputPath)

        currentVrtFile.write(currentVrtString)

        logging.info("Closing: {}".format(fullVrtFilename))
        currentVrtFile.flush()
    del currentVrtFile

    logging.info("Converting CSV to TIF")
    gdal.Grid(srcDS=fullVrtFilename
              , destName=fullOutputPath + "/" + inputFilename + ".tif"
              # as GDAL will interpolate between the points of the CSV, here we make sure, that no values are created,
              # that has not been in the original CSV file.
              , algorithm="nearest:radius1=0.0:radius2=0.0:angle=0.0:nodata=9999.0")
    os.remove(fullVrtFilename)
    logging.info("done")


def createNoDataTif(inputFile, outputFile):
    """
    Creates a raster with the same size as the given inputFile but only with NODATA values and
    writes it to outputFile

    :param inputFile: full filename to GeoTIFF
    :type inputFile: str
    :param outputFile: full filename to outpu GeoTIFF
    :type outputFile: str
    """
    logging.info("Reading raster file {}".format(inputFile))
    inputRaster = gdal.Open(inputFile)
    inputBand = inputRaster.GetRasterBand(1)
    if not inputBand.GetNoDataValue(): # if no stored NODATA value, we use 9999.0
        noDataValue = 9999.0
    else:
        noDataValue = inputBand.GetNoDataValue()

    rasterArray = inputBand.ReadAsArray()

    # replace everything in array, that is not already NoData with NoData
    rasterArray[rasterArray != noDataValue] = noDataValue

    logging.info("Creating raster with NODATA in {}".format(outputFile))
    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(outputFile,
                              inputRaster.RasterXSize,
                              inputRaster.RasterYSize,
                              1,
                              gdal.GDT_Float64)
    geotransform = inputRaster.GetGeoTransform()
    logging.debug("Geotransform: {}".format(geotransform))
    outRaster.SetGeoTransform(geotransform)

    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(rasterArray)
    outband.SetNoDataValue(noDataValue)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(inputRaster.GetProjectionRef())
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


def getValueForCoordinate(inputFile, lon, lat, noDataAsNone):
    """
    Reads the pixel value of a GeoTIFF for a geographic coordinate

    :param inputFile: full path to input GeoTIFF file
    :type inputFile: str
    :param lon: longitude
    :type lon: float
    :param lat: latitude
    :type lat: float
    :param noDataAsNone: switch to decide wether to return NODATA as None or the value stored in the GeoTIFF.
    :type noDataAsNone: bool
    :returns: pixel value of coordinate
    :rtype: float
    """
    inputRaster = gdal.Open(inputFile)
    geotransform = inputRaster.GetGeoTransform()
    rb = inputRaster.GetRasterBand(1)
    noDataVal = rb.GetNoDataValue()

    # this converts from map coordinates to raster coordinates
    # this will only work for CRS without rotation! If this is needed, we have to do some matrix
    # multiplication magic here ;-)
    px = int((lat - geotransform[0]) / geotransform[1]) # (pos - origin) / pixelsize
    py = int((lon - geotransform[3]) / geotransform[5])

    structval = rb.ReadRaster(px, py, 1, 1, buf_type=gdal.GDT_Float64)
    val = struct.unpack('d', structval) # this unpacks a C data structure into a Python value.
    if noDataAsNone and val[0] == noDataVal:
        return None
    else:
        return val[0]
