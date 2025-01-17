setwd(dirname(rstudioapi::getActiveDocumentContext()$path))
library(leaflet)
library(leafsync)
library(htmltools)
library(dplyr)
library(RColorBrewer)
library(sf)
library(leaflet.extras)
library(htmlwidgets)
library(RColorBrewer)

base_folder <- "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/"
neighborhoods <- c("Test_70_el Besòs i el Maresme")

re_sf_list <- list()

############################################################################################
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

map1
############################################################################################

cadaster_sf_list <- list()
planes_sf_list <- list()

searchPath <- "/Plane Identification/"
for (neighborhood in neighborhoods){
  parcels <- list.files(path = paste(base_folder, neighborhood, "/Parcels/", sep=""))
  for (parcel in parcels){
    constructions <- list.dirs(path = paste(base_folder, neighborhood, "/Parcels/", parcel, sep=""), recursive = FALSE, full.names = FALSE)
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
    cadaster_sf_list <- c(re_sf_list, cadaster_sf_list)
  }
}
cadaster_merged_sf <- do.call(rbind, cadaster_sf_list)
planes_merged_sf <- do.call(rbind, planes_sf_list)
paletteSilhouette <- colorNumeric(palette = c("red", "green"), domain = planes_merged_sf$silhouette)

map2 <- leaflet(planes_merged_sf, options = leafletOptions(maxZoom = 20)) %>%
  addProviderTiles(providers$OpenStreetMap.Mapnik, options = providerTileOptions(opacity=1, maxZoom=20)) %>%
  addPolygons(
    fillColor = ~ paletteSilhouette(silhouette),
    opacity = 1,
    stroke = TRUE,
    color = "black",
    fillOpacity = 1,           # Adjust the fill opacity for better visibility
    weight = 1,                 # Set outline thickness
    # label = ~format(round(silhouette, 2), nsmall = 2)
  ) %>%
  addPolygons(data = cadaster_merged_sf,
              weight = 4,
              color =  "black",
              fillColor = "white",
              fillOpacity = 0,
              opacity = 1,
              label = ~paste(REFCAT, construction, CONSTRU, sep=". ")) %>%
  addScaleBar()

map2

########################################################################################

cadaster_sf_list <- list()
panels_sf_list <- list()

searchPath <- "/Solar Estimation Panels Simulated/"
for (neighborhood in neighborhoods){
  parcels <- list.files(path = paste(base_folder, neighborhood, "/Parcels/", sep=""))
  for (parcel in parcels){
    constructions <- list.dirs(path = paste(base_folder, neighborhood, "/Parcels/", parcel, sep=""), recursive = FALSE, full.names = FALSE)
    gpkg_files <- paste0(base_folder, neighborhood, "/Parcels/", parcel, "/", constructions, "/Map files/", constructions, ".gpkg")
    
    partial_cadaster_sf_list <- lapply(gpkg_files, function(file) {
      re_sf <- read_sf(file)
      re_sf <- st_zm(re_sf)
      re_sf <- st_transform(re_sf, 4326)
      re_sf$parcel <- parcel
      re_sf$construction <- gsub(".gpkg", "", basename(file))
      re_sf$Filename <- paste(parcel, "_",gsub(".gpkg", "", basename(file)),"_Report.pdf", sep="")
      return(re_sf)
    })
    cadaster_sf_list <- c(cadaster_sf_list, partial_cadaster_sf_list)
    
    for (construction in constructions){
      planes <- list.files(path = paste0(base_folder, neighborhood, "/Parcels/", parcel, "/", construction, searchPath), recursive = FALSE, full.names = FALSE)
      planes <- planes[!file.info(file.path(paste0(base_folder, neighborhood, "/Parcels/", parcel, "/", construction, searchPath), planes))$isdir]
      planes <- planes[grepl("\\.gpkg$", planes)]
      if(length(planes) > 0){
        gpkg_files <- paste0(base_folder, neighborhood, "/Parcels/", parcel, "/", construction, searchPath, planes)
        partial_panels_sf_list <- lapply(gpkg_files, function(file) {
          re_sf <- read_sf(file)
          re_sf <- st_zm(re_sf)
          re_sf <- st_transform(re_sf, 4326)
          re_sf$parcel <- parcel
          re_sf$construction <- construction
          re_sf$plane  <- gsub(".gpkg", "", basename(file))
          return(re_sf)
        })
        panels_sf_list <- c(panels_sf_list, partial_panels_sf_list)
      }
    }
  }
}
cadaster_merged_sf <- do.call(rbind, cadaster_sf_list)
panels_merged_sf <- do.call(rbind, panels_sf_list)


palettePanels <- colorNumeric(palette = "inferno", domain = panels_merged_sf$yearly, na.color = "transparent")

map3 <- leaflet(panels_merged_sf, options = leafletOptions(maxZoom = 19)) %>%
  addProviderTiles(providers$OpenStreetMap.Mapnik, options = providerTileOptions(opacity=1, maxZoom=21)) %>%
  addPolygons(data = cadaster_merged_sf,
              weight = 8,
              color =  "black",
              fillColor = "white",
              fillOpacity = 0,
              opacity = 1,
              # label = ~paste(REFCAT, construction, CONSTRU, sep=". "
              popup = ~paste0('<h3>', gsub(".pdf", "",gsub("_Report.pdf", "", Filename)),"</h3>",
                              '<a href="data/Reports/',Filename,'"target="_blank" rel="noopener noreferrer">
                              Open the building PV potential analysis in a new tab</a>', '<br>',
                              '<br> <embed src="data/Reports/', Filename,
                              '" width="600px" height="400px"/>'),
              popupOptions = popupOptions(maxHeight = 1000, maxWidth = 1000),
              group = 'VectorReport',
  )  %>%
  addPolygons(
    data = planes_merged_sf,
    fillColor = ~ paletteSilhouette(silhouette),
    opacity = 1,
    stroke = TRUE,
    color = "black",
    fillOpacity = 1,           # Adjust the fill opacity for better visibility
    weight = 1,                 # Set outline thickness
    group = "Plane identification",
    popup = ~paste0('<h3>', paste0(parcel,"_",construction),"</h3>",
                    '<a href="data/Reports/', paste0(parcel,"_",construction,"_Report.pdf"),'"target="_blank" rel="noopener noreferrer">
                              Open the building PV potential analysis in a new tab</a>', '<br>',
                    '<br> <embed src="data/Reports/', paste0(parcel,"_",construction,"_Report.pdf"),
                    '" width="600px" height="400px"/>'),
    popupOptions = popupOptions(maxHeight = 1000, maxWidth = 1000),
  ) %>%
  
  
  addPolygons(
    data = planes_merged_sf,
    opacity = 1,
    stroke = TRUE,
    color = "black",
    fillOpacity = 0,           # Adjust the fill opacity for better visibility
    weight = 1,                 # Set outline thickness
    group = "Panels simulation"
  ) %>%
  
  
  addPolygons(
    fillColor = ~ palettePanels(yearly),
    opacity = 1,
    stroke = TRUE,
    color = "white",
    fillOpacity = 1,           # Adjust the fill opacity for better visibility
    weight = 0,                 # Set outline thickness
    group = "Panels simulation",
    popup = ~paste0('<h3>', paste0(parcel,"_",construction),"</h3>",
                    '<a href="data/Reports/', paste0(parcel,"_",construction,"_Report.pdf"),'"target="_blank" rel="noopener noreferrer">
                              Open the building PV potential analysis in a new tab</a>', '<br>',
                    '<br> <embed src="data/Reports/', paste0(parcel,"_",construction,"_Report.pdf"),
                    '" width="600px" height="400px"/>'),
    popupOptions = popupOptions(maxHeight = 1000, maxWidth = 1000),
  ) %>%
  
  addLegend(
    data = planes_merged_sf,
    pal = paletteSilhouette,
    values = ~silhouette,
    title = "Silhouette score",
    position = "bottomright",
    opacity=1,
    layerId = "Plane identification"
  )%>%
  
  addLegend(
    pal = palettePanels,
    values = ~yearly,
    title = "Solar energy production<br>(kWh/panel/year)",
    position = "bottomright",
    opacity=1,
    layerId = "Panels simulation"
  )%>%
  
  addLayersControl(
    baseGroups = c(
      "Panels simulation",
      "Plane identification"
    ),
    options = layersControlOptions(collapsed = FALSE)
  )%>%
  addScaleBar()%>%
  htmlwidgets::onRender("
    function(el, x) {
      var initialLegend = 'Panels simulation' // Set the initial legend to be displayed by layerId
      var myMap = this;
      for (var legend in myMap.controls._controlsById) {
        var el = myMap.controls.get(legend.toString())._container;
        if(legend.toString() === initialLegend) {
          el.style.display = 'block';
        } else {
          el.style.display = 'none';
        };
      };
    myMap.on('baselayerchange',
      function (layer) {
        for (var legend in myMap.controls._controlsById) {
          var el = myMap.controls.get(legend.toString())._container;
          if(legend.toString() === layer.name) {
            el.style.display = 'block';
          } else {
            el.style.display = 'none';
          };
        };
      });
    }")

map3
############################################################################################
