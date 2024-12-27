import os
import shutil

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

        
def getConstructionMap(neighborhoodPath, cadasterPath, outputResults, filterString = ""):
    directory = os.path.abspath(cadasterPath)
    city_layer  = QgsVectorLayer(directory,"City_Layer","ogr")

    directory = os.path.abspath(neighborhoodPath)
    neighborhood_layer  = QgsVectorLayer(directory,"Neighborhood_Layer","ogr")

    selection = processing.run("native:selectbylocation", {
        'INPUT':city_layer,
        'PREDICATE':[0,6],
        'INTERSECT':neighborhood_layer,
        'METHOD':0,
        'OUTPUT': 'TEMPORARY_OUTPUT',
        }
    )

    selected = city_layer.materialize(QgsFeatureRequest().setFilterFids(city_layer.selectedFeatureIds()))

    export_path = outputResults
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    QgsVectorFileWriter.writeAsVectorFormatV3(selected, export_path, QgsCoordinateTransformContext(), options)

    selected.setSubsetString(filterString)
    found_polygon_Layer = selected.materialize(QgsFeatureRequest())
    export_path = outputResults + "_FILTERED"
    QgsVectorFileWriter.writeAsVectorFormatV3(found_polygon_Layer, export_path, QgsCoordinateTransformContext(), options)


basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "70_el Besòs i el Maresme"
neighborhood = "7_P.I. Can Petit"

neighborhoodPath = basePath + "Results/Neighborhoods/" + neighborhood + ".gpkg"
neighborhoodPath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/7_P.I. Can Petit/7_P.I. Can Petit_NEIGHBORHOOD.gpkg"

cadasterPath = basePath + "Data/Cadaster/08900uA_8569_19012024_CONSTRU.ZIP"
cadasterPath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/Solar Estimation v3 - Terrassa/Data/Catastro/08279uA 8453 TERRASSA/08279uA_8453_19012024_CONSTRU.ZIP"

outputResults = basePath + "Results/" + neighborhood + "/" + neighborhood + "_CONSTRUCTIONS"
filterString = "( ((CONSTRU LIKE '%I%') AND (CONSTRU NOT LIKE '%PI%') AND (CONSTRU NOT LIKE '%CAMPING%') AND (CONSTRU NOT LIKE '%RUINA%') AND (CONSTRU NOT LIKE '%SILO%')) OR ((CONSTRU LIKE '%V%') AND (CONSTRU NOT LIKE '%VOL%') AND (CONSTRU NOT LIKE '%ZPAV%')) OR (CONSTRU LIKE '%X%') ) AND ((CONSTRU NOT LIKE '%-%') OR (CONSTRU LIKE '%+I%') OR (CONSTRU LIKE '%+V%') OR (CONSTRU LIKE '%+X%'))"
getConstructionMap(neighborhoodPath, cadasterPath, outputResults, filterString)