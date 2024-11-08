import os
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
import pandas as pd
import json

def getLidarConstructions(parcelFolder):
    for parcel in os.listdir(parcelFolder):
        directory = parcelFolder + parcel +"/" + parcel + ".laz"
        lidar_layer  = QgsPointCloudLayer(directory,"lidar_layer","pdal")
        # print(parcel)

        constructions = [f for f in os.listdir(parcelFolder + parcel) if os.path.isdir(parcelFolder + parcel + "/" + f)]
        # print('\t', constructions)

        for construction in constructions:
            directory = os.path.abspath(parcelFolder + parcel + "/" + construction + "/Map files/" + construction + ".gpkg")
            construction_layer  = QgsVectorLayer(directory,"construction_layer","ogr")
            outputPath = parcelFolder + parcel + "/" + construction + "/Map files/" + construction + ".laz"
            selection = processing.run("pdal:clip", {
                'INPUT':lidar_layer,
                'OVERLAY':construction_layer,
                'FILTER_EXPRESSION':'',
                'FILTER_EXTENT':None,
                'OUTPUT':outputPath
                }
            )

basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "70_el Besòs i el Maresme"
parcelFolder = basePath + "Results/" + neighborhood + "/Parcels/"
getLidarConstructions(parcelFolder)

