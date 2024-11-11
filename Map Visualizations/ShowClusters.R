setwd(dirname(rstudioapi::getActiveDocumentContext()$path))
library(leaflet)
library(leafsync)
library(htmltools)
library(dplyr)
library(RColorBrewer)
library(sf)

base_folder <- "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/"
neighborhoods <- c("70_el Besòs i el Maresme")


re_sf_list <- list()

###########################################################

# Create the first map

for (neighborhood in neighborhoods){
  parcels <- list.files(path = paste(base_folder, neighborhood, "/Parcels/", sep=""))
  parcels <- parcels
  for (parcel in parcels){
    constructions <- list.dirs(path = paste(base_folder, neighborhood, "/Parcels/", parcel, sep=""), recursive = FALSE, full.names = FALSE)
    gpkg_files <- paste0(base_folder, neighborhood, "/Parcels/", parcel, "/", constructions, "/Map files/", constructions, ".gpkg")
    
    partial_re_sf_list <- lapply(gpkg_files, function(file) {
      re_sf <- read_sf(file)
      re_sf <- st_zm(re_sf)
      re_sf <- st_transform(re_sf, 4326)
      re_sf$parcel <- parcel
      re_sf$construction <- gsub(".gpkg", "", basename(file))
      return(re_sf)
    })
    re_sf_list <- c(re_sf_list, partial_re_sf_list)
  }
}

merged_sf <- do.call(rbind, re_sf_list)

map1 <-leaflet(merged_sf, options = leafletOptions(maxZoom = 20)) %>%
  addProviderTiles(providers$Esri.WorldImagery, options = providerTileOptions(opacity=1, maxZoom=20)) %>%
  addProviderTiles(providers$CartoDB.VoyagerOnlyLabels) %>%
  addPolygons(weight = 4,
              color =  "blue",
              fillColor = "blue",
              fillOpacity = 0.25,
              opacity = 1,
              label = ~paste(REFCAT, construction, CONSTRU, sep=". "))%>%
  addScaleBar()

###########################################################################

# Create the second map
pointsDF_list <- data.frame()

for (neighborhood in neighborhoods){
  parcels <- list.files(path = paste(base_folder, neighborhood, "/Parcels/", sep=""))
  parcels <- parcels
  for (parcel in parcels){
    constructions <- list.dirs(path = paste(base_folder, neighborhood, "/Parcels/", parcel, sep=""), recursive = FALSE, full.names = FALSE)
    for (construction in constructions){
      clusters <- list.files(path = paste0(base_folder, neighborhood, "/Parcels/", parcel, "/", construction, "/Plane Identification/Plane Points/"), recursive = FALSE, full.names = FALSE)
      for (cluster in clusters){
        df <- read.csv(paste0(base_folder, neighborhood, "/Parcels/", parcel, "/", construction, "/Plane Identification/Plane Points/", cluster),
                       header = FALSE)
        colnames(df) <- c("x", "y", "z")
        df <- df %>% mutate(construction = construction)
        df <- df %>% mutate(cluster = cluster)
        pointsDF_list <- rbind(pointsDF_list, df)
      }
    }
  }
}

data_sf <- st_as_sf(pointsDF_list, coords = c("x", "y"), crs = 25831)
data_sf <- st_transform(data_sf, crs = 4326)


unique_clusters <- unique(data_sf$cluster)
palette <- colorFactor(palette = "Set1", domain = unique_clusters)

map2 <-leaflet(data_sf, options = leafletOptions(maxZoom = 20)) %>%
  addProviderTiles(providers$OpenStreetMap.Mapnik, options = providerTileOptions(opacity=1, maxZoom=20)) %>%
  addCircleMarkers(# Use x and y columns for coordinates
    color = ~palette(cluster),   # Color points by cluster
    label = ~cluster,            # Optional: label each point with its cluster tag
    radius = 5,                  # Adjust point size if needed
    stroke = FALSE, fillOpacity = 0.7
  )%>%
  addScaleBar()

###############################################################################################


# Use leafsync to link the maps side-by-side with synchronized movement
# Synchronize the maps
sync_map <- browsable(tagList(
  tags$style(HTML("
      html, body {width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden;}
      .leaflet-container {width: 100% !important; height: 100vh !important; float: left;}
    ")),
  sync(map1, map2)
))

# Save the synchronized map as an HTML file
htmltools::save_html(sync_map, "Cluster_map.html")

