import os
import shutil

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

        
def getParcelMap(neighborhoodPath, cadasterPath, outputResults):
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


basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/HECAPO/"
neighborhood = "HECAPO"
directory = basePath + "Results"
create_output_folder(directory)

# neighborhoodPath = basePath + "Results/Neighborhoods/" + neighborhood + ".gpkg"
# shutil.copyfile(neighborhoodPath, directory + "/" + neighborhood + "_NEIGHBORHOOD.gpkg")
cadasterPath = basePath + "/RAW_Data/08090uA_8105_19012024_PARCELA.ZIP"
#cadasterPath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/Solar Estimation v3 - Terrassa/Data/Catastro/08279uA 8453 TERRASSA/08279uA_8453_19012024_PARCELA.ZIP"
neighborhoodPath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/HECAPO/RAW_Data/Neighborhood.gpkg"
outputResults = basePath + "Results/" + neighborhood + "_PARCELS"
getParcelMap(neighborhoodPath, cadasterPath, outputResults)