import matplotlib.pyplot as plt
import numpy as np
import os
import geopandas as gpd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import ScalarFormatter


basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "Test_70_el Besòs i el Maresme"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

parcelsFolder = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/Test_70_el Besòs i el Maresme/Testing Plane ID_2/planeExtract_distance_threshold_0.45__useDistanceSampling_True_inlierThreshold_0.3_num_iterations_50/"
# parcelsFolder = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/Test_70_el Besòs i el Maresme/Testing Plane ID_2/KPlanes_distance_threshold_0.5__useDistanceSampling_True_inlierThreshold_inf_num_iterations_20/"
# parcelsFolder = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/Test_70_el Besòs i el Maresme/Testing Plane ID_2/GradientHDBSCAN_distance_threshold_0.5__squareSize_2_polar_False_minClusterSize_12/"

parcels = [parcel for parcel in os.listdir(parcelsFolder) if os.path.isdir(parcelsFolder + parcel)]
num_parcels = len(parcels)

grid_size = 3
fig, axes = plt.subplots(grid_size, grid_size, figsize=(15, 15))
fig.subplots_adjust(hspace=0.4, wspace=0.4)

colors = [(228/255.0, 38/255.0, 38/255.0), (1, 0.65, 0), (137/255.0, 239/255.0, 73/255.0)]
red_to_green = LinearSegmentedColormap.from_list("RedToGreen", colors) #["red", "orange", "green"]

min_silhouette = float('inf')  # Initialize with a very high value

for parcel in parcels:
    parcelSubfolder = parcelsFolder + parcel + "/"

    for construction in [x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)]:
        constructionFolder = parcelSubfolder + construction
        planesPath = constructionFolder + "/Plane Identification/" + construction + ".gpkg"
        planesGDF = gpd.read_file(planesPath)
        
        # Update the minimum silhouette score
        if "silhouette" in planesGDF.columns:
            min_silhouette = min(min_silhouette, planesGDF["silhouette"].min())

min_silhouette = min(min_silhouette, 0.5)

for idx, parcel in enumerate(parcels):
    row, col = divmod(idx, grid_size)  # Determine grid position
    ax = axes[row, col]  # Get the current subplot
    ax.set_title(f"{parcel}")

    parcelSubfolder = parcelsFolder + parcel + "/"

    constructions = [x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)]
    
    for construction in [x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)]:
        constructionFolder = parcelSubfolder + construction
        planesPath = constructionFolder + "/Plane Identification/" + construction + ".gpkg"
        planesGDF = gpd.read_file(planesPath)
       
        plot = planesGDF.plot(column="silhouette", edgecolor="black", cmap=red_to_green, legend=False, ax=ax, vmin=min_silhouette, vmax=1)

    ax.set_aspect('equal', 'box')
    ax.xaxis.set_major_formatter(ScalarFormatter(useOffset=True))
    ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=True))
    ax.xaxis.set_major_locator(plt.MaxNLocator(4))

fig.tight_layout()
sm = plt.cm.ScalarMappable(cmap=red_to_green, norm=plt.Normalize(vmin=min_silhouette, vmax=1))
sm._A = []  # Required for ScalarMappable
cbar = fig.colorbar(sm, ax=axes.ravel().tolist(), shrink=0.8, location='right', pad=0.05, aspect=30) 
cbar.set_label("Silhouette Score")


# Show the plot
plt.savefig("/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Scripts/Plane_Identification_Revised/nov22/plotResultsPlaneExtract.png", dpi=300)