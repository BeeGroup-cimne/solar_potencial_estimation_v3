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
pointsDF_list <- data.frame()

searchPath <- "/Plane Processing/No Overlaps/Plane Points/"
for (neighborhood in neighborhoods){
  parcels <- list.files(path = paste(base_folder, neighborhood, "/Parcels/", sep=""))
  parcels <- c("4058610DF3845G", "4554301DF3845D", "4251517DF3845A")
  for (parcel in parcels){
    constructions <- list.dirs(path = paste(base_folder, neighborhood, "/Parcels/", parcel, sep=""), recursive = FALSE, full.names = FALSE)
    # constructions <- constructions[4]
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
    
    for (construction in constructions){
      clusters <- list.files(path = paste0(base_folder, neighborhood, "/Parcels/", parcel, "/", construction, searchPath), recursive = FALSE, full.names = FALSE)
      for (cluster in clusters){
        df <- read.csv(paste0(base_folder, neighborhood, "/Parcels/", parcel, "/", construction, searchPath, cluster),
                       header = FALSE)
        colnames(df) <- c("x", "y", "z")
        df <- df %>% mutate(construction = construction)
        df <- df %>% mutate(cluster = cluster)
        pointsDF_list <- rbind(pointsDF_list, df)
      }
    }
  }
}
merged_sf <- do.call(rbind, re_sf_list)

data_sf <- st_as_sf(pointsDF_list, coords = c("x", "y"), crs = 25831)
data_sf <- st_transform(data_sf, crs = 4326)


unique_clusters <- unique(data_sf$cluster)
palette <- colorFactor(palette = "Set1", domain = unique_clusters)

map2 <-leaflet(data_sf, options = leafletOptions(maxZoom = 25)) %>%
  addProviderTiles(providers$OpenStreetMap.Mapnik, options = providerTileOptions(opacity=1, maxZoom=20)) %>%
  addCircleMarkers(# Use x and y columns for coordinates
    color = ~palette(cluster),   # Color points by cluster
    radius = 5,                  # Adjust point size if needed
    stroke = FALSE, fillOpacity = 1
  ) %>%
  addPolygons(data = merged_sf,
              weight = 2,
              color =  "black",
              fillColor = "black",
              fillOpacity = 0.25,
              opacity = 1,
              label = ~paste(REFCAT, construction, CONSTRU, sep=". ")) %>%
  addScaleBar() %>%
  addLegend(
    "bottomright",                # Position of the legend
    pal = palette,                # Color palette
    values = ~cluster,            # Values used for the legend (clusters)
    title = "Cluster",            # Title for the legend
    opacity = 1                   # Legend opacity
  )

map2