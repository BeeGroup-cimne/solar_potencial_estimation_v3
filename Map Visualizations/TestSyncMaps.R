# setwd(dirname(rstudioapi::getActiveDocumentContext()$path))
library(leaflet)
library(leafsync)
library(htmltools)
library(dplyr)
library(RColorBrewer)
library(sf)
library(leaflet.extras)
library(htmlwidgets)

base_folder <- "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/"
neighborhoods <- c("Test_70_el Besòs i el Maresme")
neighborhoods <- c("70_el Besòs i el Maresme")
# neighborhoods <- c("7_P.I. Can Petit")


re_sf_list <- list()

###########################################################

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
              color =  "black",
              fillColor = "blue",
              fillOpacity = 0,
              opacity = 1,
              label = ~paste(REFCAT, construction, CONSTRU, sep=". "))%>%
  addScaleBar()

###########################################################################

# Create the second map
cadaster_sf_list <- list()
planes_sf_list <- list()

searchPath <- "/Plane Identification/"
for (neighborhood in neighborhoods){
  parcels <- list.files(path = paste(base_folder, neighborhood, "/Parcels/", sep=""))
  # parcels <- c("4058610DF3845G", "4554301DF3845D", "4251517DF3845A")
  for (parcel in parcels){
    constructions <- list.dirs(path = paste(base_folder, neighborhood, "/Parcels/", parcel, sep=""), recursive = FALSE, full.names = FALSE)
    # gpkg_files <- paste0(base_folder, neighborhood, "/Parcels/", parcel, "/", constructions, "/Map files/", constructions, ".gpkg")
    # 
    # partial_cadaster_sf_list <- lapply(gpkg_files, function(file) {
    #   re_sf <- read_sf(file)
    #   re_sf <- st_zm(re_sf)
    #   re_sf <- st_transform(re_sf, 4326)
    #   re_sf$parcel <- parcel
    #   re_sf$construction <- gsub(".gpkg", "", basename(file))
    #   return(re_sf)
    # })
    # cadaster_sf_list <- c(cadaster_sf_list, partial_cadaster_sf_list)
    
    for (construction in constructions){
      planes <- list.files(
        path = paste0(base_folder, neighborhood, "/Parcels/", parcel, "/", construction, searchPath), 
        recursive = FALSE, 
        full.names = FALSE, 
        pattern = "\\.gpkg$"
      )
      if(length(planes) > 0){
        gpkg_files <- paste0(base_folder, neighborhood, "/Parcels/", parcel, "/", construction, searchPath, planes)
        partial_planes_sf_list <- lapply(gpkg_files, function(file) {
          re_sf <- read_sf(file)
          re_sf <- st_zm(re_sf)
          re_sf <- st_transform(re_sf, 4326)
          re_sf$parcel <- parcel
          re_sf$construction <- construction
          re_sf$plane  <- gsub(".gpkg", "", basename(file))
          return(re_sf)
        })
        planes_sf_list <- c(planes_sf_list, partial_planes_sf_list)
      }
    }
  }
}
# cadaster_merged_sf <- do.call(rbind, cadaster_sf_list)
planes_merged_sf <- do.call(rbind, planes_sf_list)

library(RColorBrewer)
palette <- colorNumeric(palette = c("red", "green"), domain = planes_merged_sf$silhouette)

map2 <- leaflet(planes_merged_sf, options = leafletOptions(maxZoom = 20)) %>%
  addProviderTiles(providers$OpenStreetMap.Mapnik, options = providerTileOptions(opacity=1, maxZoom=20)) %>%
  addPolygons(
    fillColor = ~ palette(silhouette),
    opacity = 1,
    stroke = TRUE,
    color = "black",
    fillOpacity = 1,           # Adjust the fill opacity for better visibility
    weight = 1                 # Set outline thickness
  ) %>%
  # addPolygons(data = cadaster_merged_sf,
  #             weight = 4,
  #             color =  "black",
  #             fillColor = "white",
  #             fillOpacity = 0,
  #             opacity = 1,
  #             label = ~paste(REFCAT, construction, CONSTRU, sep=". ")) %>%
  addScaleBar()

# map2
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
sync_map
# !!!!! You need to save the hmlt "by hand". Display sync_map on the viewer and then Export > Save as Web Page

library(plotly)
# saveWidget(as_widget(sync_map), "synchronized_map.html")


# install.packages("servr")
library(servr)
# Save the map to an HTML file
html_file <- "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Map Visualizations/remoteSync.html"
saveWidget(map2, file = html_file, selfcontained = TRUE)

# Serve the map using servr and print the port
# server <- servr::httd(dir = dirname(html_file), browse = FALSE)
# cat("Server running at:", server$url, "\n")