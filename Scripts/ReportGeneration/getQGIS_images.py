import json
import pandas as pd
import numpy as np
import csv
import os
import math
import shutil 
from tqdm import tqdm

import geopandas as gpd
import laspy

def get_layer_centroid(layer):
    if not layer.isValid():
        print("Layer is not valid")
        return None

    layer.updateExtents()  # Ensure the layer's spatial extents are up to date
    features = list(layer.getFeatures())  # Get all features in the layer

    if not features:
        print("No features in layer")
        return None

    combined_geom = QgsGeometry.unaryUnion([feat.geometry() for feat in features])  # Merge geometries
    if combined_geom is None or combined_geom.isEmpty():
        print("Geometry is empty")
        return None

    centroid = combined_geom.centroid()
    return centroid.asPoint()  # Returns QgsPointXY

    
def getZoomOut(construction, constructionFolder, reportFolder,  offset=250):
    def finished_zoomOut():
        img = render.renderedImage()
        img.save(reportFolder + "ZoomOut.png")

    cadasterPath = constructionFolder + "/Map files/" + construction + ".gpkg"
    cadasterGDF = gpd.read_file(cadasterPath)

    QgsProject.instance().clear()

    # Image 1: Map View with cadaster outline
    tms = 'type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0'
    OSMlayer = QgsRasterLayer(tms, 'OSM', 'wms')
    QgsProject.instance().addMapLayer(OSMlayer)

    cadasterLayer = QgsVectorLayer(cadasterPath,"Neighborhood_layer","ogr")
    single_symbol_renderer = cadasterLayer.renderer()
    symbol = single_symbol_renderer.symbol()
    symbol.setColor(QColor.fromRgb(0,0,0,0))
    symbol.symbolLayer(0).setStrokeColor(QColor(255,0,0,255))
    symbol.symbolLayer(0).setStrokeWidth(1)
    QgsProject.instance().addMapLayer(cadasterLayer)


    settings = QgsMapSettings()
    settings.setLayers(QgsProject.instance().mapLayers().values())
    settings.setOutputSize(QSize(1000,1000))
    centroidx, centroidy = cadasterGDF.centroid.x[0], cadasterGDF.centroid.y[0]
    settings.setExtent(QgsRectangle(centroidx-offset, centroidy-offset, centroidx+offset, centroidy+offset))
    settings.setDestinationCrs(cadasterLayer.crs())

    render = QgsMapRendererParallelJob(settings)
    render.finished.connect(finished_zoomOut)
    render.start()
    render.waitForFinished()

def getZoomIn(construction, constructionFolder, reportFolder, buffer=2.5):
    def finished_ZoomIn():
        img = render.renderedImage()
        img.save(reportFolder + "ZoomIn.png")



    QgsProject.instance().clear()

    cadasterPath = constructionFolder + "/Map files/" + construction + ".gpkg"
    cadasterGDF = gpd.read_file(cadasterPath)
    
    
    # Image 2: Satellite View with cadaster outline
    # map = 'type=xyz&zmin=0&zmax=19&url=https://mt1.google.com/vt/lyrs=s%26x={x}%26y={y}%26z={z}'
    map = 'type=xyz&zmin=0&zmax=19&url=https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
    OSMlayer = QgsRasterLayer(map, 'map', 'wms')
    QgsProject.instance().addMapLayer(OSMlayer)

    cadasterLayer = QgsVectorLayer(cadasterPath,"Neighborhood_layer","ogr")
    single_symbol_renderer = cadasterLayer.renderer()
    symbol = single_symbol_renderer.symbol()
    symbol.setColor(QColor.fromRgb(0,0,0,0))
    symbol.symbolLayer(0).setStrokeColor(QColor(255,0,0,255))
    symbol.symbolLayer(0).setStrokeWidth(1)
    QgsProject.instance().addMapLayer(cadasterLayer)

    settings = QgsMapSettings()
    settings.setLayers(QgsProject.instance().mapLayers().values())
    settings.setOutputSize(QSize(1000,1000))
    [minx, miny, maxx, maxy] = cadasterGDF.total_bounds
    centroidx, centroidy = cadasterGDF.centroid.x[0], cadasterGDF.centroid.y[0]
    settings.setExtent(QgsRectangle(minx-buffer, miny-buffer, maxx+buffer, maxy+buffer))
    settings.setDestinationCrs(cadasterLayer.crs())

    render = QgsMapRendererParallelJob(settings)
    render.finished.connect(finished_ZoomIn)
    render.start()
    render.waitForFinished()


# parcel = "4054901DF3845C"
# construction = "408"
    
    
basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "70_el Besòs i el Maresme"
neighborhood = "HECAPO"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

for parcel in tqdm(os.listdir(parcelsFolder), desc="Parcels", leave=True):
    parcelSubfolder = parcelsFolder + parcel + "/"
    # for construction in tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)],  desc="Constructions", leave=False):
    for construction in [x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)]:
        constructionFolder = parcelSubfolder + construction + "/"
        reportFolder = constructionFolder + "Report Files/"
            
        getZoomOut(construction, constructionFolder, reportFolder)
        getZoomIn(construction, constructionFolder, reportFolder)
