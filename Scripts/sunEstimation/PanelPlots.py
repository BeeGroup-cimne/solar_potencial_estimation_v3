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
import matplotlib.colors as mcolors

import warnings
warnings.filterwarnings("ignore")

basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "Test_70_el Besòs i el Maresme"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

fig, axs = plt.subplots(3, 3, figsize=(15, 15))

parcels = os.listdir(parcelsFolder)     

    
maxProduction = 400
minProduction = 800

# for i, parcel in enumerate(parcels):
#     subfolder = parcelsFolder + "/" + parcel + "/"

#     for construction in [x for x in os.listdir(subfolder) if os.path.isdir(subfolder + x)]:
#         panelGDFpath = parcelsFolder + parcel + "/" + construction + "/Solar Estimation Panels Simulated/" + construction + ".gpkg"
#         if os.path.isfile(panelGDFpath):
#             panelGDF = gpd.read_file(panelGDFpath)
#             panelGDF = panelGDF.dropna()

#             minProduction = np.minimum(minProduction, panelGDF["yearly"].min())
#             maxProduction = np.maximum(maxProduction, panelGDF["yearly"].max())


for i, parcel in enumerate(parcels):
    subfolder = parcelsFolder + "/" + parcel + "/"
    
    ax = axs[i // 3, i % 3]     
    norm = mcolors.BoundaryNorm(np.arange(200, 700, 50), ncolors=256)

    panelsGDFs = []

    for construction in [x for x in os.listdir(subfolder) if os.path.isdir(subfolder + x)]:
        panelGDFpath = parcelsFolder + parcel + "/" + construction + "/Solar Estimation Panels Simulated/" + construction + ".gpkg"
        if os.path.isfile(panelGDFpath):
            panelsGDFs.append(gpd.read_file(panelGDFpath))

    combined_gdf = gpd.GeoDataFrame(pd.concat(panelsGDFs, ignore_index=True))

    combined_gdf.plot(ax = ax, column='yearly', edgecolor="white", linewidth=0.25,
                    cmap='gnuplot', norm=norm)
                        
    ax.set_aspect('equal')
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.set_title(parcel)

    ax.xaxis.set_major_formatter(ScalarFormatter(useOffset=True))
    ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=True))
    ax.xaxis.set_major_locator(plt.MaxNLocator(4))

    for construction in [x for x in os.listdir(subfolder) if os.path.isdir(subfolder + x)]:
        gpkgFile = subfolder + construction + "/Plane Identification/" + construction + ".gpkg"    
        planesGDF = gpd.read_file(gpkgFile)
        planesGDF.plot(ax=ax, color='none', edgecolor='black')

    for construction in [x for x in os.listdir(subfolder) if os.path.isdir(subfolder + x)]:
        gpkgFile = subfolder + construction + "/Map files/" + construction + ".gpkg"    
        cadasterGDF = gpd.read_file(gpkgFile)
        cadasterGDF.plot(ax=ax, color='none', edgecolor='black', linewidth=4)


sm = plt.cm.ScalarMappable(cmap="gnuplot", norm=norm)
sm._A = []  # Required for ScalarMappable
cbar = fig.colorbar(sm, ax=axs.ravel().tolist(), shrink=0.8, location='right', pad=0.05, aspect=30) 
cbar.set_label("kWh/panel/year")


# Show the plot
plt.savefig("/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Scripts/sunEstimation/PanelPlots.png",bbox_inches='tight', dpi=300)
plt.show()