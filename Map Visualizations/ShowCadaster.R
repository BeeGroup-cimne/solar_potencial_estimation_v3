setwd(dirname(rstudioapi::getActiveDocumentContext()$path))
library(leaflet)
library(readr)
library(dplyr)
library(sf)      # For reading the GeoPackages
library(htmltools)


base_folder <- "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/"
neighborhoods <- c("70_el Besòs i el Maresme")


re_sf_list <- list()

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
  addScaleBar(position = "topright")
map1

htmlwidgets::saveWidget(map1, "El Besòs i el Maresme - Cadaster Map.html", title = "Cadaster Map")
