import os
import laspy
import numpy as np
import matplotlib.pyplot as plt
import tqdm
import geopandas as gpd

base_path = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/Test_70_el Besòs i el Maresme/Testing Plane ID_2/"
base_export_path = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/Test_70_el Besòs i el Maresme/Testing Plane Information/V2/Images/"

for experiment in tqdm.tqdm(os.listdir(base_path)):
    fig, axes = plt.subplots(3, 3, figsize=(15, 15), dpi=200)
    axes = axes.flatten()

    experiment_folder = base_path + experiment + "/"
    for idx, parcel in enumerate([x for x in os.listdir(experiment_folder) if os.path.isdir(experiment_folder+x)]):
        parcel_folder = experiment_folder + parcel + "/"
        for construction in os.listdir(parcel_folder):
            lasDF = laspy.read(parcel_folder + construction + "/Plane Identification/" + construction + ".laz")
            gpkgFile = parcel_folder + construction + "/Plane Identification/" + construction + ".gpkg"
            try:
                planeID = gpd.read_file(gpkgFile)
                clusters = planeID.cluster.values

                x = lasDF.x
                y = lasDF.y
                classification = lasDF.classification
                # classification = np.where(classification == 255, -1, classification)

                mask = np.isin(classification, clusters)
                x_filtered = x[mask]
                y_filtered = y[mask]
                classification_filtered = classification[mask]

                scatter = axes[idx].scatter(x_filtered, y_filtered, c=classification_filtered, cmap='viridis', s=1, alpha=0.6)
            except:
                pass

        axes[idx].set_title(parcel)
        axes[idx].set_xlabel("x")
        axes[idx].set_ylabel("y")
        axes[idx].set_aspect("equal")

    # Adjust layout and show the plot
    export_path = base_export_path + experiment + ".png"
    fig.suptitle(experiment)
    plt.savefig(export_path, dpi=200)
    plt.close()