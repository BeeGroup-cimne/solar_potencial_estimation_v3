import os 

basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/70_el Besòs i el Maresme/Parcels/"
total = 0
for parcel in os.listdir(basePath):
    for construction in [x for x in os.listdir(basePath+parcel) if os.path.isdir(basePath+parcel+"/"+x)]:
        constructionFolder = basePath+parcel+"/"+construction+"/"
        panelFolder = constructionFolder + "Solar Estimation Panels"
        if(not os.path.isdir(panelFolder)):
            print(parcel, construction)
            total = total +1

print(total)