import os
import shutil

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

# Step 1: split by neighborhood
def split_neighborhoods(mapPath, outputFolder):
    directory = outputFolder
    create_output_folder(directory)

    directory = os.path.abspath(mapPath)
    city_layer  = QgsVectorLayer(directory,"City_Layer","ogr")
    # QgsProject.instance().addMapLayer(city_layer, True)

    print("Segmenting by each neighborhood, this might take some seconds")

    for feature in city_layer.getFeatures():
        identifier = feature.attributes()[feature.fieldNameIndex('fid')]
        file_name = str(identifier) + "_" + feature.attributes()[feature.fieldNameIndex('nom_barri')]

        city_layer.setSubsetString(f"fid={identifier}")
        found_polygon_Layer = city_layer.materialize(QgsFeatureRequest())

        file_name = file_name.replace(" / ", "_")

        export_path = outputFolder + file_name
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        QgsVectorFileWriter.writeAsVectorFormatV3(found_polygon_Layer, export_path, QgsCoordinateTransformContext(), options)



basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
mapPath = basePath + "Data/Barcelona_Neighborhoods.gpkg"
outputFolder = basePath + "Results/Neighborhoods/"
split_neighborhoods(mapPath, outputFolder)