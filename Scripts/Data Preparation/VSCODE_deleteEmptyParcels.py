import os
import shutil

def deleteEmptyParcels(directory):
    for folder in os.listdir(directory):
        currentFolder = directory + folder + "/"
        constructionsCount = len([f for f in os.listdir(currentFolder) if os.path.isdir(currentFolder + f)])
        if(constructionsCount == 0):
            print(folder)
            shutil.rmtree(currentFolder)

if __name__ == "__main__":
    basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
    neighborhood = "70_el Besòs i el Maresme"
    neighborhood = "7_P.I. Can Petit"
    directory = basePath + "Results/" + neighborhood + "/Parcels/"
    deleteEmptyParcels(directory)