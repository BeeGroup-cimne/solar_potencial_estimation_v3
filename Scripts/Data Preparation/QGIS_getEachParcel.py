import os
import shutil

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

def getEachParcel(mapPath, buildingsFolder):
    directory = buildingsFolder
    create_output_folder(directory)

    directory = os.path.abspath(mapPath)
    neighborhood_layer  = QgsVectorLayer(directory,"Neighborhood_layer","ogr")


    for feature in neighborhood_layer.getFeatures():
        identifier = feature.attributes()[feature.fieldNameIndex('REFCAT')]
        fileFolder = buildingsFolder + "/" + str(identifier)
        create_output_folder(fileFolder, deleteFolder = True)

        neighborhood_layer.setSubsetString(f"REFCAT='{identifier}'")
        found_polygon_Layer = neighborhood_layer.materialize(QgsFeatureRequest())

        export_path = fileFolder + "/" + str(identifier)

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        QgsVectorFileWriter.writeAsVectorFormatV3(found_polygon_Layer, export_path, QgsCoordinateTransformContext(), options)


basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "70_el Besòs i el Maresme"
neighborhood = "7_P.I. Can Petit"

mapPath = basePath + "Results/" + neighborhood + "/" + neighborhood + "_PARCELS.gpkg"
mapPath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/7_P.I. Can Petit/7_P.I. Can Petit_PARCELS.gpkg"
buildingsFolder = basePath + "Results/" + neighborhood + "/Parcels"
getEachParcel(mapPath, buildingsFolder)