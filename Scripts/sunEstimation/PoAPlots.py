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
    
    maxPoA = 0
    for construction in [x for x in os.listdir(subfolder) if os.path.isdir(subfolder + x)]:
        poaPath = subfolder + construction + "/Solar Estimation PySAM_POA_Yearly/"
        poaFiles = os.listdir(poaPath)
        poaDF = pd.DataFrame()
        for poaFile in poaFiles:
            try:
                filePath = os.path.join(poaPath, poaFile)
                temp_df = pd.read_csv(filePath)  # Read the CSV file
                poaDF = pd.concat([poaDF, temp_df], ignore_index=True)  # Concatenate into the main dataframe
            except:
                pass

        poaDF = poaDF.dropna()
        z = poaDF["annual"]
        if(not np.isnan(z.max())):
            maxPoA = np.maximum(maxPoA, z.max())
            
    allPoA = pd.DataFrame()
    for construction in [x for x in os.listdir(subfolder) if os.path.isdir(subfolder + x)]:
        poaPath = subfolder + construction + "/Solar Estimation PySAM_POA_Yearly/"
        poaFiles = os.listdir(poaPath)
        poaDF = pd.DataFrame()

        for poaFile in poaFiles:
            try:
                filePath = os.path.join(poaPath, poaFile)
                temp_df = pd.read_csv(filePath)  # Read the CSV file
                poaDF = pd.concat([poaDF, temp_df], ignore_index=True)  # Concatenate into the main dataframe
            except:
                print(parcel, construction, poaFile)
                pass

        poaDF = poaDF.dropna()
        allPoA = pd.concat([allPoA, poaDF], ignore_index=True)

    x = allPoA["x"]
    y = allPoA["y"]
    z = allPoA["annual"]

    # Create a grid for x and y
    xi = np.linspace(min(x), max(x), math.ceil(max(x)-min(x)))
    yi = np.linspace(min(y), max(y), math.ceil(max(y)-min(y)))
    xi, yi = np.meshgrid(xi, yi)

    # Interpolate z onto the grid
    zi = griddata((x, y), z, (xi, yi), method='linear')

    tree = cKDTree(np.c_[x, y])  # KDTree for distance computation
    distances, _ = tree.query(np.c_[xi.ravel(), yi.ravel()], k=1)  # Find nearest point distances
    distances = distances.reshape(xi.shape)  # Reshape to grid shape
    zi = np.ma.masked_where(distances > 2.5, zi)  # Mask zi where the distance is greater than 2m

    # Plot the mesh
    ax = axs[i // 3, i % 3]
    z_levels = np.arange(np.floor(z.min()/50)*50, np.ceil(z.max()/50)*50+1, 50)  # From 1300 to 1800 in steps of 100
    if(len(z_levels) < 3):
        z_levels = np.arange(np.floor(z.min()), np.ceil(z.max())+1, np.ceil(z.max())-np.floor(z.min()))
    elif(len(z_levels) < 6):
        z_levels = np.arange(np.floor(z.min()/20)*20, np.ceil(z.max()/20)*20+1, 20)

    # z_levels = np.arange(1000, 1901, 100)  # From 1300 to 1800 in steps of 100
    heatmap = ax.contourf(xi, yi, zi, levels=z_levels, cmap='gnuplot')
    # heatmap = ax.contourf(xi, yi, zi, levels=100, cmap='gnuplot')
    cb = fig.colorbar(heatmap, ax=ax, label="kWh/m\u00b2/year")

    cbar_ticks = cb.ax.get_yticks()  # Get current colorbar ticks
            
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

# Show the plot
plt.savefig("/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Scripts/sunEstimation/PoAPlots.png",bbox_inches='tight',dpi=300)
plt.show()