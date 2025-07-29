import geopandas as gpd

from utils import create_output_folder

def extract_parcels(gpkgFilePath, outputFolder):
    parcelGDF = gpd.read_file(gpkgFilePath)
    for _, row in parcelGDF.iterrows():
        name = row["REFCAT"]
        exportFolder = outputFolder + "/" + name + "/"
        create_output_folder(exportFolder, deleteFolder=True)
        
        singleParcelGDF = gpd.GeoDataFrame([row], crs=parcelGDF.crs)
        singleParcelGDF.to_file(exportFolder + name + ".gpkg")

def extract_constructions(gpkgFilePath, outputFolder, filter=True):
    constructionGDF = gpd.read_file(gpkgFilePath)

    if(filter):
        mask = (
            (
                constructionGDF["CONSTRU"].str.contains("I") &
                ~constructionGDF["CONSTRU"].str.contains("PI|CAMPING|RUINA|SILO")
            ) |
            (
                constructionGDF["CONSTRU"].str.contains("V") &
                ~constructionGDF["CONSTRU"].str.contains("VOL|ZPAV")
            ) |
            constructionGDF["CONSTRU"].str.contains("X")
        ) & (
            ~constructionGDF["CONSTRU"].str.contains("-") |
            constructionGDF["CONSTRU"].str.contains(r"\+I|\+V|\+X")
        )
        constructionGDF = constructionGDF[mask]

    parcelList = constructionGDF["REFCAT"].unique()
    for parcel in parcelList:
        subsetGDF = constructionGDF[constructionGDF["REFCAT"] == parcel]
        for _, row in subsetGDF.iterrows():
            name = str(int(row["NINTERNO"]))
            exportFolder = outputFolder + "/" + parcel + "/" + name + "/Map files/"
            create_output_folder(exportFolder)

            singleConstructionGDF = gpd.GeoDataFrame([row], crs=constructionGDF.crs)
            singleConstructionGDF.to_file(exportFolder + name + ".gpkg")
