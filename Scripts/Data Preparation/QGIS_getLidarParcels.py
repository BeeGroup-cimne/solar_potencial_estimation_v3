import os
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
import pandas as pd
import json

def getLidarParcels(parcelFolder, listPath, lazPath, mergedPath):
    lidarsNeeded_df = pd.read_csv(listPath)
    lidarsNeeded_df.files = lidarsNeeded_df.files.apply(json.loads)
    lidarsNeeded_df.bounds = lidarsNeeded_df.bounds.apply(json.loads)

    # get those depending on only a LiDAR file
    just1file_df = lidarsNeeded_df[lidarsNeeded_df.file_count == 1]
    just1file_df.files = just1file_df.files.apply(lambda x: x[0])

    for currentfile in just1file_df.files.unique():
        print(currentfile)
        directory = lazPath + currentfile + ".laz"
        lidar_layer  = QgsPointCloudLayer(directory,"lidar_layer","pdal")
        # QgsProject.instance().addMapLayer(lidar_layer)
        
        selected_cadasters = just1file_df[just1file_df.files == currentfile]
        
        for cadasterFile in selected_cadasters.REFCAT:
            directory = os.path.abspath(parcelFolder + cadasterFile + "/" + cadasterFile + ".gpkg")
            parcel_layer  = QgsVectorLayer(directory,"parcel_layer","ogr")
            # QgsProject.instance().addMapLayer(parcel_layer)

            outputPath = parcelFolder + cadasterFile + "/" + cadasterFile + ".laz"
            selection = processing.run("pdal:clip", {
                'INPUT':lidar_layer,
                'OVERLAY':parcel_layer,
                'FILTER_EXPRESSION':'',
                'FILTER_EXTENT':None,
                'OUTPUT':outputPath
                }
            )

    print("Single file cases done")
    # do the rest
    multipleFiles_df = lidarsNeeded_df[~(lidarsNeeded_df.file_count == 1)]
    merged_layer  = QgsPointCloudLayer(mergedPath,"lidar_layer","pdal")
    for cadasterFile in multipleFiles_df.REFCAT:
        print(cadasterFile)
        directory = os.path.abspath(parcelFolder + cadasterFile + "/" + cadasterFile + ".gpkg")
        parcel_layer  = QgsVectorLayer(directory,"parcel_layer","ogr")
        
        outputPath = parcelFolder + cadasterFile + "/" + cadasterFile + ".laz"
        selection = processing.run("pdal:clip", {
            'INPUT':merged_layer,
            'OVERLAY':parcel_layer,
            'FILTER_EXPRESSION':'',
            'FILTER_EXTENT':None,
            'OUTPUT':outputPath
            }
        )


basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "70_el Besòs i el Maresme"
parcelFolder = basePath + "Results/" + neighborhood + "/Parcels/"
lazPath = basePath + "RAW_Data/LiDAR/"
listPath = basePath + "Results/" + neighborhood + "/necessaryLiDAR.txt"
mergedPath = basePath + "Data/Merged_LiDAR.laz"
getLidarParcels(parcelFolder, listPath, lazPath, mergedPath)

