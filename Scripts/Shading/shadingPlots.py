import matplotlib.pyplot as plt
import numpy as np
import os
import geopandas as gpd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import ScalarFormatter
import math
import pandas as pd

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
from scipy.spatial import cKDTree
from matplotlib.colors import Normalize
import matplotlib.patches as mpatches
from matplotlib.cm import ScalarMappable

import warnings
warnings.filterwarnings("ignore")

basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "Test_70_el Besòs i el Maresme"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

fig, axs = plt.subplots(3, 3, figsize=(20, 20))

parcels = os.listdir(parcelsFolder)
          

for i, parcel in enumerate(parcels):
    subfolder = parcelsFolder + "/" + parcel + "/"
    
    max_shade = 0
    for construction in [x for x in os.listdir(subfolder) if os.path.isdir(subfolder + x)]:
        shadingPath = subfolder + construction + "/Shading/"
        shadingFiles = os.listdir(shadingPath)
        shadingProfiles = pd.DataFrame()
        for shadingFile in shadingFiles:
            try:
                filePath = os.path.join(shadingPath, shadingFile)
                temp_df = pd.read_csv(filePath, header=None)  # Read the CSV file
                shadingProfiles = pd.concat([shadingProfiles, temp_df], ignore_index=True)  # Concatenate into the main dataframe
            except:
                pass
        shadingProfiles['avg'] = shadingProfiles.iloc[:, 3:363].mean(axis=1)
        shadingProfiles = shadingProfiles.dropna()
        z = shadingProfiles["avg"]
        max_shade = np.maximum(max_shade, z.max())

    for construction in [x for x in os.listdir(subfolder) if os.path.isdir(subfolder + x)]:
        shadingPath = subfolder + construction + "/Shading/"
        # shadingFiles = ["1.csv", "2.csv", "3.csv"]
        shadingFiles = os.listdir(shadingPath)

        shadingProfiles = pd.DataFrame()

        ax = axs[i // 3, i % 3]

        for shadingFile in shadingFiles:
            try:
                filePath = os.path.join(shadingPath, shadingFile)
                temp_df = pd.read_csv(filePath, header=None)  # Read the CSV file
                shadingProfiles = pd.concat([shadingProfiles, temp_df], ignore_index=True)  # Concatenate into the main dataframe
            except:
                # print(parcel, construction, shadingFile)
                pass

        shadingProfiles['avg'] = shadingProfiles.iloc[:, 3:363].mean(axis=1)
        shadingProfiles = shadingProfiles.rename(columns={0:"x", 1:"y"})
        shadingProfiles["x"] = np.array(shadingProfiles["x"], dtype=float)
        shadingProfiles["y"] = np.array(shadingProfiles["y"], dtype=float)

        shadingProfiles = shadingProfiles.dropna()

        # Assuming shadingsProfiles is a dictionary-like object
        x =  np.array(shadingProfiles["x"], dtype=float)
        y =  np.array(shadingProfiles["y"], dtype=float)
        z = shadingProfiles["avg"]

        # Create a grid for x and y
        xi = np.linspace(min(x), max(x), math.ceil(max(x)-min(x)))
        yi = np.linspace(min(y), max(y), math.ceil(max(y)-min(y)))
        xi, yi = np.meshgrid(xi, yi)

        # Interpolate z onto the grid
        zi = griddata((x, y), z, (xi, yi), method='cubic')

        tree = cKDTree(np.c_[x, y])  # KDTree for distance computation
        distances, _ = tree.query(np.c_[xi.ravel(), yi.ravel()], k=1)  # Find nearest point distances
        distances = distances.reshape(xi.shape)  # Reshape to grid shape

        zi = np.ma.masked_where(distances > 2.5, zi)  # Mask zi where the distance is greater than 2m
        
        heatmap = ax.contourf(xi, yi, zi, vmin=0, vmax=max_shade, cmap='gray_r')

    norm = Normalize(vmin=0, vmax=max_shade)
    cbar = fig.colorbar(ScalarMappable(norm=norm, cmap='gray_r'), ax=ax)
    cbar.set_label('Average shading angle')
    cbar_ticks = cbar.ax.get_yticks()  # Get current colorbar ticks
    # cbar.ax.set_yticks(cbar_ticks[0:-1])  # Ensure the same ticks are used
    cbar.ax.set_yticklabels([f"{tick:.0f}°" for tick in cbar_ticks])  # Add ° to each tick

        
            
    ax.set_aspect('equal')
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.set_title(parcel)

    ax.xaxis.set_major_formatter(ScalarFormatter(useOffset=True))
    ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=True))
    ax.xaxis.set_major_locator(plt.MaxNLocator(4))

    for construction in [x for x in os.listdir(subfolder) if os.path.isdir(subfolder + x)]:
        gpkgFile = subfolder + construction + "/Map files/" + construction + ".gpkg"
        
        cadasterGDF = gpd.read_file(gpkgFile)
        cadasterGDF.plot(ax=ax, color='none', edgecolor='none')


# Add axis labels and title

# Show the plot
plt.savefig("/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Scripts/Shading/shadingPlots.png",bbox_inches='tight', dpi=300)
plt.show()