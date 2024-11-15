import pandas as pd
from tqdm import tqdm
import os

from Scripts.Plane_Identification_Revised.mergePlanes import merge_planes
from Scripts.Plane_Identification_Revised.splitPlanes import split_planes
from Scripts.Plane_Identification_Revised.deletePlanes import delete_planes
from Scripts.Plane_Identification_Revised.fitCadaster import fit_cadaster

if __name__ == "__main__":
    basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
    neighborhood = "Test_70_el Besòs i el Maresme"
    parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

    parcelsList = []
    constructionsList = []
    elapsedTimesList = []
    for parcel in tqdm(os.listdir(parcelsFolder)):
        parcelPath = parcelsFolder + parcel
        for construction in [x for x in os.listdir(parcelPath) if os.path.isdir(parcelPath + "/" + x)]:
            constructionFolder = parcelPath + "/" + construction + "/"
            try:
                elapsed_time = merge_planes(constructionFolder)
                elapsed_time += split_planes(constructionFolder)
                elapsed_time += delete_planes(constructionFolder)
                elapsed_time += fit_cadaster(constructionFolder)
                elapsedTimesList.append(elapsed_time)
                parcelsList.append(parcel)
                constructionsList.append(construction)

            except Exception as e:
                print(parcel, construction, e)

    summaryDF = pd.DataFrame({
    'parcel': parcelsList,
    'construction': constructionsList,
    'time': elapsedTimesList
    })

    print(summaryDF.head())