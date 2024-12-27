import os
import shutil

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

        
# Step 1: get buildings from the neighborhood
def getEachConstruction(constructionMapPath, parcelsFolder):
    directory = os.path.abspath(constructionMapPath)
    construction_layer  = QgsVectorLayer(directory,"Construction","ogr")

    for parcel in os.listdir(parcelsFolder):
        # print(parcel)

        directory = os.path.abspath(parcelsFolder + parcel +"/" + parcel + ".gpkg")
        parcel_layer  = QgsVectorLayer(directory,"Parcel_Layer","ogr")
        

        selection = processing.run("native:selectbylocation", {
            'INPUT':construction_layer,
            'PREDICATE':[6],
            'INTERSECT':parcel_layer,
            'METHOD':0,
            'OUTPUT': 'TEMPORARY_OUTPUT',
            }
        )

        selected = construction_layer.materialize(QgsFeatureRequest().setFilterFids(construction_layer.selectedFeatureIds()))
        # QgsProject.instance().addMapLayer(selected)

        for feature in selected.getFeatures():
            identifier = feature.attributes()[feature.fieldNameIndex('fid')]
            # print('\t' + str(identifier))
            create_output_folder(parcelsFolder + parcel + "/" + str(identifier), deleteFolder=True)
            fileFolder = parcelsFolder + parcel + "/" + str(identifier) + "/Map files/"
            create_output_folder(fileFolder, deleteFolder=True)

            selected.setSubsetString(f"fid='{identifier}'")
            found_polygon_Layer = selected.materialize(QgsFeatureRequest())

            export_path = fileFolder + "/" + str(identifier)

            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            QgsVectorFileWriter.writeAsVectorFormatV3(found_polygon_Layer, export_path, QgsCoordinateTransformContext(), options)


basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "70_el Besòs i el Maresme"
neighborhood = "7_P.I. Can Petit"

constructionMapPath = basePath + "Results/" + neighborhood + "/" + neighborhood + "_CONSTRUCTIONS_FILTERED.gpkg"
parcelsFolder = basePath + "Results/" + neighborhood + "/Parcels/"
getEachConstruction(constructionMapPath, parcelsFolder)