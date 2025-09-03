import geopandas as gpd
import matplotlib.pyplot as plt

def plot_identified_planes(experimentPath, parcel, construction):
    parcelPath = experimentPath + "/" + parcel + "/"
    constructionPath = parcelPath + str(construction) + "/"
    gpkgPath = constructionPath + "Plane Identification/" + construction + ".gpkg"
    geoDF = gpd.read_file(gpkgPath)
    geoDF.plot(column = "cluster", legend = True)
    plt.show()

def plot_parcel_planeID(experimentPath, parcel):
    pass

def plot_yearly_panels(experimentPath, parcel, construction):
    parcelPath = experimentPath + "/" + parcel + "/"
    constructionPath = parcelPath + str(construction) + "/"

    fig, ax = plt.subplots()

    gpkgPath = constructionPath + "Solar Estimation Panels Simulated/" + construction + ".gpkg"
    geoDF = gpd.read_file(gpkgPath)
    geoDF.plot(column = "yearly", legend = True, cmap="inferno", ax=ax)
    cadasterPath = constructionPath + "Map files/" + construction + ".gpkg"
    cadasterGDF = gpd.read_file(cadasterPath)
    cadasterGDF.plot(facecolor="none", edgecolor="black", ax=ax)
    plt.show()


wd = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Final Version/"
resultsPath = wd + "Results/"
experimentPath = resultsPath + "Experiment 1/"
parcel = "4054901DF3845C"
construction = "115084364"

plot_yearly_panels(experimentPath, parcel, construction)