import logging
from osgeo import gdal, osr
import os

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
    :return: nothing
    """
    # make input and output path absolute in case it is not already
    fullInputPath = os.path.abspath(inputPath)
    fullOutputPath = os.path.abspath(outputPath)

    fullVrtFilename = fullOutputPath + "/" + inputFilename +".vrt"
    #    fullInputFilename = fullInputPath + "/" + inputFileName

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
    gdal.Grid(srcDS=fullVrtFilename,
              destName=fullOutputPath + "/" + inputFilename + ".tif",
              algorithm="invdist:power=2.0:smoothing=0.01:radius1=1.0:radius2=1.0:angle=0.0:max_points=0:min_points=0:nodata=9999.0")
    os.remove(fullVrtFilename)
    logging.info("done")

def createNoDataTif(inputFile, outputFile):
    """
    Creates a raster with the same size as the given inputFile but only with NODATA values and
    writes it to outputFile
    :param inputFile: full filename to GeoTIFF
    :param outputFile: full filename to outpu GeoTIFF
    """
    logging.info("Reading raster file {}".format(inputFile))
    inputRaster = gdal.Open(inputFile)
    inputBand = inputRaster.GetRasterBand(1)
    if not inputBand.GetNoDataValue():
        noDataValue = 9999.0
    else:
        noDataValue = inputBand.GetNoDataValue()

    rasterArray = inputBand.ReadAsArray()

    #replace everything in array, that is not already NoData with NoData
    rasterArray[rasterArray != noDataValue] = noDataValue

    logging.info("Creating raster with NODATA in {}".format(outputFile))
    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(outputFile,
                              inputRaster.RasterXSize,
                              inputRaster.RasterYSize,
                              1,
                              gdal.GDT_Float64)
    geotransform = inputRaster.GetGeoTransform()
    outRaster.SetGeoTransform((geotransform[0], #x origin
                               geotransform[1], #pixel width
                               0,
                               geotransform[3], #y origin
                               0,
                               geotransform[5]))#pixel height

    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(rasterArray)
    outband.SetNoDataValue(noDataValue)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(inputRaster.GetProjectionRef())
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()
