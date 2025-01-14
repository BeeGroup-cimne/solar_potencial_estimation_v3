import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import math
import geopandas as gpd
import os

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, PageBreak
from reportlab.platypus import Paragraph, PageBreak, SimpleDocTemplate
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.units import mm
from pypdf import PdfMerger
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping

from PyPDF2 import PdfWriter, PdfReader 
import io

# Bounds definition, units in mm
breatherV = 2
breatherH = 2.5
sectionSpacer = 5
sectionTitleHeight = 11 #points
textHeight = 9 #points
sectionTitleSpacer = 2 #mm
horizontalMargin = 20
# Header
headerMargin = 30
headerTextHeight = 12.5
#fig: 1089px * 478px
logoRatio = 1089/478
headerLogoPosition = 22.5
headerLogoHeight = 15  
headerLogoWidth = headerLogoHeight*logoRatio  
# Title
titleTextHeight = 5
# Map
mapFigSide = 55
textLineSeparation = 5
# Found roofs
# roofFigSide = 60
roofFigSide = 75
roofBigFigSide = 90
# planeCellWidths = [15, 25, 25, 25]
# planeCellWidths = [5, 5, 20, 32, 10, 18]
planeCellWidths = [5, 5, 20, 27, 10, 18]
rowHeight = 5.5
# Energy Summary
heatmapFigSide = 75
summaryCellWidths = [5, 30, 15, 35]
# Energy Detail
heatmapPlaneFigSide = 75
heatmapCellWidths = [10.5, 29.5, 14.5, 32.5]

# Composed variables
mapOrigin = headerMargin + textLineSeparation + sectionSpacer
planesOrigin = mapOrigin + breatherV + textLineSeparation + breatherV + mapFigSide + breatherV + textLineSeparation + sectionSpacer
energyOrigin = planesOrigin + breatherV + roofFigSide + breatherV + sectionSpacer

# For summary table
buildingSummaryFieldsWidth = [18, 12, 29.5, 28.5, 17, 16, 16, 33] #id, region, municipality, road, road number, lat, long, state
buildingSummaryFieldsWidth = [18, 29.5, 28.5, 17, 16, 16, 16, 16, 33] #identifier, Municipality, Road, Road number, long, lat, Name, Owner, Simulation results
buildingSummaryFieldsWidth = [17, 26.5, 26, 16, 14.5, 14.5, 45, 30] #identifier, Municipality, Road, Road number, long, lat, Name, Simulation results


# For table of contents
tableOrigin = mapOrigin
tableBegin = tableOrigin + breatherV
tableEnd = 297-tableBegin

rowsPerPage = (tableEnd-tableBegin)/rowHeight

rowsPerPage = (math.floor(rowsPerPage))

def signFromDirection(value):
    direction = value[-1]
    number = value[:-1]
    if direction == 'E' or direction == 'N':    return float(number)
    elif direction == 'W' or direction == 'S':  return -float(number)
    else:   return value

class CanvasWriter(): 

    def __init__(self, filename):
        self.canvas_page = canvas.Canvas(filename, pagesize=A4, bottomup=0) #bottomup=0 to place origin in topLeft

        pdfmetrics.registerFont(TTFont('Arial', r"C:\Users\jaasb\INVESTIGO\BEE Group\eplanet shared\Programa Final\Samples and Test\Automated Report Test\arial-font\arial.ttf"))
        addMapping('Arial', 0, 0, 'Arial')
        pdfmetrics.registerFont(TTFont('ArialItallic', r"C:\Users\jaasb\INVESTIGO\BEE Group\eplanet shared\Programa Final\Samples and Test\Automated Report Test\arial-font\G_ari_i.TTF"))
        addMapping('ArialItallic', 0, 0, 'ArialItallic')
    
    def set_header(self, reportTitle, logo):
        # Text
        self.canvas_page.setFillColor(colors.black)
        self.canvas_page.setFont("Helvetica", 8)
        self.canvas_page.drawString(horizontalMargin*mm,(headerMargin-headerTextHeight)*mm, reportTitle)
        # Logo
        self.canvas_page.saveState()
        self.canvas_page.scale(1,-1)
        self.canvas_page.drawImage(logo, (210-horizontalMargin-headerLogoWidth)*mm, -(headerMargin-headerLogoPosition)*mm, width=headerLogoWidth*mm, height=-headerLogoHeight*mm)
        self.canvas_page.restoreState()

    def set_title(self, name):
        self.canvas_page.setFillColor(colors.black)
        self.canvas_page.setFont("Helvetica-Bold", 14)
        
        # text_width = stringWidth(name)
        self.canvas_page.drawCentredString(105*mm,(headerMargin-sectionTitleSpacer)*mm, name)

        #canvas_page.setLineWidth(5)
        p = self.canvas_page.beginPath()
        p.moveTo(horizontalMargin*mm,headerMargin*mm)
        p.lineTo((210-horizontalMargin)*mm,headerMargin*mm)
        p.close()
        self.canvas_page.setLineWidth(2)
        self.canvas_page.drawPath(p)

    def line(self, xmin, ymin, xmax, ymax):
        self.canvas_page.setFillColor(colors.black)
        p = self.canvas_page.beginPath()
        p.moveTo(xmin*mm,ymin*mm)
        p.lineTo(xmax*mm,ymax*mm)
        p.close()
        self.canvas_page.setLineWidth(0.1)
        self.canvas_page.drawPath(p)

    def addSectionTitle(self, text, x, y):
        self.canvas_page.setFillColor(colors.black)
        self.canvas_page.setFont("Helvetica-BoldOblique", sectionTitleHeight)
        self.canvas_page.drawString(x*mm,y*mm, ('\t ' + text)) #('\t' + text) creates a dark square

    def display_fig(self, imagePath, xmin, ymin, width, height):
        self.canvas_page.saveState()
        self.canvas_page.scale(1,-1)
        self.canvas_page.drawImage(imagePath, xmin*mm, -ymin*mm, width=width*mm, height=-height*mm)
        self.canvas_page.restoreState()

    def location_info(self, lat, long):
        self.canvas_page.setFillColor(colors.black)
        self.canvas_page.setFont("Helvetica", textHeight)
        
        if(type(lat) == type("40.00N")):
            lat = signFromDirection(lat)

        if(type(long) == type("40.00N")):
            long = signFromDirection(long)
        
        latname = "%.05f"%(abs(lat))
        if(lat > 0): latname = latname + " N"
        else: latname = latname + " S"
 
        longname = "%.05f"%(abs(long))
        if(long > 0): longname = longname + " E"
        else: longname = longname + " W"
    
        # self.canvas_page.drawString(horizontalMargin*mm, (mapOrigin+breatherV+mapFigSide+breatherV+textLineSeparation)*mm, "Coordinates:")
        # self.canvas_page.drawString(horizontalMargin*mm, (mapOrigin+breatherV+mapFigSide+breatherV+2*textLineSeparation)*mm, latname+longname)
        self.canvas_page.drawString(horizontalMargin*mm, (mapOrigin+textLineSeparation+breatherV+mapFigSide+breatherV+textLineSeparation*0.5)*mm, latname + ", " + longname)
        # self.canvas_page.drawString(horizontalMargin*mm, (mapOrigin+breatherV+mapFigSide+breatherV+2*textLineSeparation)*mm, direction)
        # self.canvas_page.drawCentredString((horizontalMargin+mapFigSide/2)*mm, (mapOrigin+breatherV+mapFigSide+breatherV+textLineSeparation)*mm, latname+longname)

    def building_info(self, cadastrePath, pointCloudPath): #buildingPath, buildingID
        # Get area
        cadatreLimits = gpd.read_file(cadastrePath)
        area = cadatreLimits.geometry[0].area
        # Get LiDAR info
        pointCloud = pd.read_csv(pointCloudPath, header=None)
        nPoints = len(pointCloud)
        # Display info
        self.canvas_page.setFont("Helvetica", textHeight)
        textline1 = "Building area: %.0f m\u00b2"%area
        self.canvas_page.drawString((horizontalMargin+mapFigSide+breatherH)*mm, (mapOrigin+textLineSeparation+breatherV+mapFigSide+breatherV+textLineSeparation*0.5)*mm, textline1)

        textline2 = "%.0f"%nPoints + " LiDAR points (%.2f points/m\u00b2)"%(nPoints/area)
        self.canvas_page.drawString((horizontalMargin+2*mapFigSide+2*breatherH)*mm, (mapOrigin+textLineSeparation+breatherV+mapFigSide+breatherV+textLineSeparation*0.5)*mm, textline2)

    def mapSection(self, mapPath, satPath, LiDARPath, lat, long, direction, cadastrePath, pointCloudPath):
        self.line(horizontalMargin,mapOrigin, (210-horizontalMargin), mapOrigin)
        self.addSectionTitle("Location information",horizontalMargin, mapOrigin-sectionTitleSpacer)
        self.canvas_page.setFont("ArialItallic", textHeight*0.875)
        self.canvas_page.drawRightString((210-horizontalMargin)*mm, (mapOrigin + textLineSeparation)*mm, direction)
        self.canvas_page.setFont("Helvetica", textHeight)
        
        self.display_fig(mapPath, (horizontalMargin), (mapOrigin+textLineSeparation+breatherV), mapFigSide, mapFigSide)
        self.display_fig(satPath, (horizontalMargin+mapFigSide+breatherH), (mapOrigin+textLineSeparation+breatherV), mapFigSide, mapFigSide)
        self.display_fig(LiDARPath, (horizontalMargin+2*mapFigSide+2*breatherH), (mapOrigin+textLineSeparation+breatherV), mapFigSide, mapFigSide)

        scaleZoomOut = r"C:\Users\jaasb\INVESTIGO\BEE Group\eplanet shared\Programa Final\Samples and Test\Automated Report Test\ScaleZoomOut.png"
        scaleZoomIn = r"C:\Users\jaasb\INVESTIGO\BEE Group\eplanet shared\Programa Final\Samples and Test\Automated Report Test\ScaleZoomIn.png"
        self.display_fig(scaleZoomOut, (horizontalMargin+breatherH/2), (mapOrigin+textLineSeparation+breatherV+mapFigSide-mapFigSide*1.1/10 - breatherH/2), mapFigSide*6/10, mapFigSide*1.1/10)
        # self.display_fig(scaleZoomIn, (horizontalMargin+mapFigSide+breatherH+breatherH/2), (mapOrigin+breatherV+mapFigSide-mapFigSide*1.1/10 - breatherH/2), mapFigSide*6/10, mapFigSide*1.1/10)

        self.location_info(lat, long)
        self.building_info(cadastrePath, pointCloudPath)

    def mapSectionEmpty(self, mapPath, satPath, lat, long, direction):
        self.line(horizontalMargin,mapOrigin, (210-horizontalMargin), mapOrigin)
        self.addSectionTitle("Location information",horizontalMargin, mapOrigin-sectionTitleSpacer)
        self.canvas_page.setFont("ArialItallic", textHeight*0.875)
        self.canvas_page.drawRightString((210-horizontalMargin)*mm, (mapOrigin + textLineSeparation)*mm, direction)
        self.canvas_page.setFont("Helvetica", textHeight)

        self.display_fig(mapPath, (horizontalMargin), (mapOrigin+textLineSeparation+breatherV), mapFigSide, mapFigSide)
        self.display_fig(satPath, (horizontalMargin+mapFigSide+breatherH), (mapOrigin+textLineSeparation+breatherV), mapFigSide, mapFigSide)
        
        scaleZoomOut = r"C:\Users\jaasb\INVESTIGO\BEE Group\eplanet shared\Programa Final\Samples and Test\Automated Report Test\ScaleZoomOut.png"
        scaleZoomIn = r"C:\Users\jaasb\INVESTIGO\BEE Group\eplanet shared\Programa Final\Samples and Test\Automated Report Test\ScaleZoomIn.png"
        self.display_fig(scaleZoomOut, (horizontalMargin+breatherH/2), (mapOrigin+textLineSeparation+breatherV+mapFigSide-mapFigSide*1.1/10 - breatherH/2), mapFigSide*6/10, mapFigSide*1.1/10)
        # self.display_fig(scaleZoomIn, (horizontalMargin+mapFigSide+breatherH+breatherH/2), (mapOrigin+breatherV+mapFigSide-mapFigSide*1.1/10 - breatherH/2), mapFigSide*6/10, mapFigSide*1.1/10)

        self.location_info(lat, long)
        textline2 = "LiDAR file was empty"
        self.canvas_page.drawString((horizontalMargin+2*mapFigSide+2*breatherH)*mm, (mapOrigin+breatherV+mapFigSide+breatherV+textLineSeparation)*mm, textline2)

    def badQualityLabel(self):
        self.canvas_page.setFont("Helvetica-Bold", textHeight*2)
        self.canvas_page.drawCentredString((110)*mm, (mapOrigin+breatherV+mapFigSide+3*(breatherV+textLineSeparation))*mm, "LiDAR data does not fulfill quality requirements")


    def printPlaneTable(self, planedf, fields, fieldNames, planePointList, x, y):
        table = planedf[fields]
        table_reversed = table.iloc[::-1]

        # data = [[index] + ["%.2f"%element for element in row[0:3]] for index, row in table.iterrows()]
        data = [["", index] + ["%.1f"%element for element in row[0:4]] for index, row in table_reversed.iterrows()] + [fieldNames[0:1] + [""] + fieldNames[1:5]]
        t=Table(data, colWidths=[planeCellWidths[i]*mm for i in range(len(planeCellWidths))], rowHeights=[rowHeight*mm for i in range(len(data))])
        
        style = TableStyle([('ALIGN', (0,0), (5, len(data)),'RIGHT'),
                            ('ALIGN', (0,0), (1, len(data)),'LEFT'),
                            ('FONTNAME', (0, 0), (1, len(data)), 'Helvetica-Bold'),
                            ('FONTNAME', (0, -1), (5, -1), 'Helvetica-Bold'),
                            ('LINEABOVE', (0, -1), (5, -1), 1, colors.black),
                            ('FONTSIZE', (0, 0), (5, len(data)), textHeight),
                            ('BOTTOMPADDING', (0, 0), (5, len(data)), 8),
                            ('VALIGN', (0, 0), (5, len(data)),'BOTTOM'),
        ])
        t.setStyle(style)
        
        color = iter(plt.cm.rainbow(np.linspace(0, 1, len(planedf))))

        for each in range(len(planedf)):
            if each % 2 == 1:   bg_color = colors.whitesmoke
            else:   bg_color = colors.white
            t.setStyle(TableStyle([('BACKGROUND', (0, each), (5, each), bg_color)]))
        
        sm = plt.cm.rainbow(np.linspace(0, 1, len(planedf)))

        rgb_tuples = []
        for i in range(len(planedf)):
            rgb_color = sm[len(planedf)-1-i][:3] # Get RGB values
            rgb_tuples.append((rgb_color[0], rgb_color[1], rgb_color[2]))
            t.setStyle(TableStyle([('BACKGROUND', (0, i), (0, i), colors.toColor(rgb_tuples[i]))]))

        self.canvas_page.saveState()
        self.canvas_page.scale(1,1)
        t.wrapOn(self.canvas_page, sum(planeCellWidths)*mm, (len(data))*rowHeight*mm)
        t.drawOn(self.canvas_page, x*mm, y*mm)
        self.canvas_page.restoreState()

    def planeSection(self, planedf, fields, planePointList, planeFigPath): 
        self.line(horizontalMargin, planesOrigin, (210-horizontalMargin), planesOrigin)
        self.addSectionTitle("Identified rooftops",horizontalMargin, planesOrigin-sectionTitleSpacer)
        self.display_fig(planeFigPath, (horizontalMargin), (planesOrigin+breatherV), roofFigSide, roofFigSide)
        centeringMargin = 0.5*(breatherV+roofFigSide - (1+len(planedf)*rowHeight)) 
        fieldNames = ["Plane", "Area (m\u00b2)", "Avg. height (m)", "Tilt(\u00b0)", "Azimuth(\u00b0)"]
        self.printPlaneTable(planedf, fields, fieldNames, planePointList, (horizontalMargin+roofFigSide+2*breatherH), (planesOrigin+centeringMargin))

    def planeSectionLarge(self, planedf, fields, planePointList, planeFigPath): 
        self.line(horizontalMargin, planesOrigin, (210-horizontalMargin), planesOrigin)
        self.addSectionTitle("Identified rooftops",horizontalMargin, planesOrigin-sectionTitleSpacer)
        self.display_fig(planeFigPath, (horizontalMargin), (planesOrigin+breatherV), roofFigSide, roofFigSide)
        fieldNames = ["Plane", "Area (m\u00b2)", "Avg. height (m)", "Tilt(\u00b0)", "Azimuth(\u00b0)"]
        self.printPlaneTable(planedf, fields, fieldNames, planePointList, (horizontalMargin+roofFigSide+2*breatherH), (planesOrigin+breatherV))
        
    def energySummaryTable(self, energyTable, x, y):
        units = ["(kWh/m\u00b2/year)", "", "(m\u00b2)", "(MWh/year)"]
        data = [["", row[0]] + ["%.1f"%element for element in row[1:2]] + ["%.3f"%element for element in row[2:3]] for index, row in energyTable.iterrows()] + [list(units)] + [list(energyTable.columns.values[0:1]) + [" "] + list(energyTable.columns.values[1:3])]
        t=Table(data, colWidths=[summaryCellWidths[i]*mm for i in range(len(summaryCellWidths))], rowHeights=[rowHeight*mm for i in range(len(data))])
    
        style = TableStyle([('ALIGN', (0,0), (3, len(data)),'RIGHT'),
                            ('ALIGN', (0,0), (1, len(data)),'LEFT'),
                            ('FONTNAME', (1, 0), (1, len(data)), 'Helvetica-Bold'),
                            ('FONTNAME', (0, -2), (3, -1), 'Helvetica-Bold'),
                            ('LINEABOVE', (0, -2), (3, -2), 1, colors.black),
                            ('FONTSIZE', (0, 0), (3, len(data)), textHeight),
                            ('BOTTOMPADDING', (0, 0), (3, len(data)), 8),
                            ('VALIGN', (0, 0), (3, len(data)),'BOTTOM'),
                            ('LINEBELOW', (0, 0), (3, 0), 1, colors.black),
                            ('FONTNAME', (0,0), (3, 0), 'Helvetica-Bold'),
        ])
        t.setStyle(style)

        cmap = mpl.cm.plasma
        bounds = list(range(80, 241, 20))
        norm = mpl.colors.BoundaryNorm(bounds, cmap.N, extend='both')
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm) 
        sm.set_array([]) 

        for each in range(1,len(energyTable)):
            if each % 2 == 0:   bg_color = colors.whitesmoke
            else:   bg_color = colors.white
            t.setStyle(TableStyle([('BACKGROUND', (0, each), (3, each), bg_color)]))

        rgb_arrays = []
        for i in range(len(bounds)):
            rgb_color = sm.to_rgba(bounds[len(bounds)-1-i])[:3]  # Get RGB values
            rgb_arrays.append(rgb_color)
            t.setStyle(TableStyle([('BACKGROUND', (0, i+1), (0, i+1), colors.toColor(rgb_color))]))
        
        # t.setStyle(TableStyle([('BACKGROUND', (0, 0), (3, 0), colors.whitesmoke)]))

        self.canvas_page.saveState()
        self.canvas_page.scale(1,1)
        t.wrapOn(self.canvas_page, sum(heatmapCellWidths)*mm, (len(data))*rowHeight*mm)
        t.drawOn(self.canvas_page, x*mm, y*mm)
        self.canvas_page.restoreState()

    def energySummarySection(self, heatmapFigPath, summaryEnergydf):
        self.line(horizontalMargin, energyOrigin, (210-horizontalMargin), energyOrigin)
        self.addSectionTitle("Energy prediction - Summary",horizontalMargin, energyOrigin-sectionTitleSpacer)
        self.display_fig(heatmapFigPath, (horizontalMargin), (energyOrigin+breatherV), heatmapFigSide, heatmapFigSide)
        centeringMargin = 0.5*(breatherV+heatmapFigSide - (2+len(summaryEnergydf)*rowHeight)) 
        self.energySummaryTable(summaryEnergydf, (horizontalMargin+heatmapFigSide+2*breatherH), (energyOrigin+centeringMargin))

    def energySummarySectionLarge(self, heatmapFigPath, summaryEnergydf):
        self.line(horizontalMargin, mapOrigin, (210-horizontalMargin), mapOrigin)
        self.addSectionTitle("Energy prediction - Summary",horizontalMargin, mapOrigin-sectionTitleSpacer)
        self.display_fig(heatmapFigPath, (110 -heatmapFigSide*1.5/2), (mapOrigin+breatherV), heatmapFigSide*1.5, heatmapFigSide*1.5)
        centeringMargin = 0.5*(breatherV+heatmapFigSide - (2+len(summaryEnergydf)*rowHeight)) 
        self.energySummaryTable(summaryEnergydf, (110 - sum(heatmapCellWidths)/2), (mapOrigin+2*breatherV+heatmapFigSide*1.5))

    def detailTable(self, sidedf, x, y):
        units = ["(kWh/m\u00b2/year)", "(m\u00b2)", "(MWh/year)"]
        data = []
        if(len(sidedf)):
            for i in range(len(sidedf)):
                detaildf = sidedf[len(sidedf)-1-i]
                detaildf = detaildf.reindex(index=detaildf.index[::-1])
                
                
                # data = data + [[row[0], row[1]] + ["%.1f"%element for element in row[2:3]] + ["%.3f"%element for element in row[3:4]] for index, row in detaildf.iterrows()]
                data =  data + [["", row[1]] + ["%.1f"%element for element in row[2:3]] + ["%.3f"%element for element in row[3:4]] for index, row in detaildf.iloc[0:len(detaildf)-1].iterrows()]
                data = data + [[row[0], row[1]] + ["%.1f"%element for element in row[2:3]] + ["%.3f"%element for element in row[3:4]]  for index, row in detaildf.iloc[len(detaildf)-1:len(detaildf)].iterrows()]
            data = data + [[''] + list(units[0:3])]
            data = data + [list(detaildf.columns.values)]
            t=Table(data, colWidths=[heatmapCellWidths[i]*mm for i in range(len(heatmapCellWidths))], rowHeights=[rowHeight*mm for i in range(len(data))])
            
            style = TableStyle([('ALIGN', (0,0), (3, len(data)),'RIGHT'),
                                ('ALIGN', (0,0), (1, len(data)),'LEFT'),
                                ('FONTNAME', (0, 0), (0, len(data)), 'Helvetica-Bold'),
                                ('FONTNAME', (0, -2), (3, -1), 'Helvetica-Bold'),
                                ('LINEABOVE', (0, -2), (3, -2), 1, colors.black),
                                ('FONTSIZE', (0, 0), (3, len(data)), textHeight),
                                ('FONTSIZE', (0, -1), (3, -1), 0.95*textHeight),
                                ('BOTTOMPADDING', (0, 0), (3, len(data)), 8),
                                ('VALIGN', (0, 0), (3, len(data)),'BOTTOM'),
            ])
            t.setStyle(style)

            currentPos = 0
            for i in range(len(sidedf)):
                detaildf = sidedf[len(sidedf)-1-i]
                style = TableStyle([('FONTNAME', (0, currentPos), (3, currentPos), 'Helvetica-Bold'),
                                ('LINEABOVE', (0, currentPos), (3, currentPos), 1, colors.black),
                ])
                t.setStyle(style)
                currentPos = currentPos + len(detaildf)
       
            t.wrapOn(self.canvas_page, sum(heatmapCellWidths)*mm, (len(data))*rowHeight*mm)
            t.drawOn(self.canvas_page, x*mm, y*mm)
        
    def energyDetailSection(self, heatmapPlanesFigPath, leftdf, rightdf):
        PageBreak().drawOn(self.canvas_page, 0, mapOrigin-sectionTitleSpacer)
        self.line(horizontalMargin, mapOrigin, (210-horizontalMargin), mapOrigin)
        self.addSectionTitle("Energy prediction - Detail",horizontalMargin, mapOrigin-sectionTitleSpacer)
        self.display_fig(heatmapPlanesFigPath, (210-heatmapPlaneFigSide)/2, (mapOrigin+breatherV), heatmapPlaneFigSide, heatmapPlaneFigSide)  
        self.detailTable(leftdf, (horizontalMargin), (mapOrigin+breatherV+heatmapPlaneFigSide+breatherV))  
        self.detailTable(rightdf, (210/2 + 2*breatherH), (mapOrigin+breatherV+heatmapPlaneFigSide+breatherV)) 

    def energyDetailSectionLarge(self, heatmapPlanesFigPath, leftdf, rightdf, position):
        PageBreak().drawOn(self.canvas_page, 0, mapOrigin-sectionTitleSpacer)
        self.line(horizontalMargin, mapOrigin, (210-horizontalMargin), mapOrigin)
        self.addSectionTitle("Energy prediction - Detail " + position, horizontalMargin, mapOrigin-sectionTitleSpacer)
        self.display_fig(heatmapPlanesFigPath, (210-heatmapPlaneFigSide)/2, (mapOrigin+breatherV), heatmapPlaneFigSide, heatmapPlaneFigSide)  
        self.detailTable(leftdf, (horizontalMargin), (mapOrigin+breatherV+heatmapPlaneFigSide+breatherV))  
        self.detailTable(rightdf, (210/2 + 2*breatherH), (mapOrigin+breatherV+heatmapPlaneFigSide+breatherV))  

    def writePageNumber(self, pagenumber):
        self.canvas_page.setFont("Helvetica-Oblique", textHeight)
        if(pagenumber%2 == 0):
            # self.canvas_page.drawString((horizontalMargin)*mm, (297-horizontalMargin*3/4)*mm, "page " + str(pagenumber))
            self.canvas_page.drawString((horizontalMargin)*mm, (297-horizontalMargin*3/4)*mm, str(pagenumber))
        else:
            # self.canvas_page.drawRightString((210-horizontalMargin)*mm, (297-horizontalMargin*3/4)*mm, "page " + str(pagenumber))
            self.canvas_page.drawRightString((210-horizontalMargin)*mm, (297-horizontalMargin*3/4)*mm, str(pagenumber))
            
    def writeBuildingTable(self, partialTabledf, x=horizontalMargin, y=tableBegin):
        self.canvas_page.setFont("Arial", textHeight)
        table_reversed = partialTabledf.iloc[::-1]
        data = [[element for element in row] for index, row in table_reversed.iterrows()] +  [partialTabledf.columns.values]
        data
        t=Table(data, colWidths=[buildingSummaryFieldsWidth[i]*mm for i in range(len(buildingSummaryFieldsWidth))], rowHeights=[rowHeight*mm for i in range(len(data))])

        style = TableStyle([('ALIGN', (0,0), (len(buildingSummaryFieldsWidth), len(data)),'LEFT'),
                            ('FONTNAME', (0, 0), (len(buildingSummaryFieldsWidth), len(data)), 'Arial'),
                            ('FONTNAME', (0, -1), (len(buildingSummaryFieldsWidth), -1), 'Helvetica-Bold'),
                            ('LINEABOVE', (0, -1), (len(buildingSummaryFieldsWidth), -1), 1, colors.black),
                            ('FONTSIZE', (0, 0), (len(buildingSummaryFieldsWidth), len(data)), 0.75*textHeight*0.9),
                            ('BOTTOMPADDING', (0, 0), (len(buildingSummaryFieldsWidth), len(data)), 8),
                            ('VALIGN', (0, 0), (len(buildingSummaryFieldsWidth), len(data)),'BOTTOM'),
        ])
        t.setStyle(style)

        for each in range(len(partialTabledf)):
            if each % 2 == 1:   bg_color = colors.whitesmoke
            else:   bg_color = colors.white
            t.setStyle(TableStyle([('BACKGROUND', (0, each), (len(buildingSummaryFieldsWidth), each), bg_color)]))

        self.canvas_page.saveState()
        self.canvas_page.scale(1,1)
        t.wrapOn(self.canvas_page, sum(buildingSummaryFieldsWidth)*mm, (len(data))*rowHeight*mm)
        t.drawOn(self.canvas_page, x*mm, y*mm)
        self.canvas_page.restoreState()

    @staticmethod
    def watermark(originPath, destinationPath, reportTitle, logo, startingPage):
        existing_pdf = PdfReader(open(originPath, "rb"))
        output = PdfWriter()

        for i in range(len(existing_pdf.pages)):
            # Odd
            packetFront = io.BytesIO()
            canvas_pageFront = canvas.Canvas(packetFront, pagesize=A4, bottomup=0)
            # Text
            canvas_pageFront.setFillColor(colors.black)
            canvas_pageFront.setFont("Helvetica", 8)
            canvas_pageFront.drawString(horizontalMargin*mm,(headerMargin-headerTextHeight)*mm, reportTitle)
            # Logo
            canvas_pageFront.saveState()
            canvas_pageFront.scale(1,-1)
            canvas_pageFront.drawImage(logo, (210-horizontalMargin-headerLogoWidth)*mm, -(headerMargin-headerLogoPosition)*mm, width=headerLogoWidth*mm, height=-headerLogoHeight*mm)
            canvas_pageFront.restoreState()

            canvas_pageFront.setFont("Helvetica-Oblique", textHeight)
                # canvas_pageFront.drawString((horizontalMargin)*mm, (297-horizontalMargin*3/4)*mm, str(pagenumber))
            canvas_pageFront.drawRightString((210-horizontalMargin)*mm, (297-horizontalMargin*3/4)*mm, str(startingPage+i))
            canvas_pageFront.save()

            # Even
            packetBack = io.BytesIO()
            canvas_pageBack = canvas.Canvas(packetBack, pagesize=A4, bottomup=0)            
            # Text
            canvas_pageBack.setFillColor(colors.black)
            canvas_pageBack.setFont("Helvetica", 8)
            canvas_pageBack.drawString(horizontalMargin*mm,(headerMargin-headerTextHeight)*mm, reportTitle)
            # Logo
            canvas_pageBack.saveState()
            canvas_pageBack.scale(1,-1)
            canvas_pageBack.drawImage(logo, (210-horizontalMargin-headerLogoWidth)*mm, -(headerMargin-headerLogoPosition)*mm, width=headerLogoWidth*mm, height=-headerLogoHeight*mm)
            canvas_pageBack.restoreState()

            canvas_pageBack.setFont("Helvetica-Oblique", textHeight)
            canvas_pageBack.drawString((horizontalMargin)*mm, (297-horizontalMargin*3/4)*mm, str(startingPage+i))
            canvas_pageBack.save()

            #move to the beginning of the StringIO buffer   
            packetFront.seek(0)

            # create a new PDF with Reportlab
            new_pdfFront = PdfReader(packetFront)
            new_pdfBack = PdfReader(packetBack)
            
        
            page = existing_pdf.pages[i]
            if((i+1) % 2 == 1): #Odd
                page.merge_page(new_pdfFront.pages[0])
            else: #Even
                page.merge_page(new_pdfBack.pages[0])
            output.add_page(page)

        output_stream = open(destinationPath, "wb")
        output.write(output_stream)
        output_stream.close()

    @staticmethod
    def split_table(summaryTabledf):
        tableSplit = []
        for i in range(math.ceil(len(summaryTabledf)/rowsPerPage)): 
            lowerlim = rowsPerPage*i
            upperlim = min(rowsPerPage*(i+1), len(summaryTabledf))
            tableSplit.append(summaryTabledf[lowerlim:upperlim])
        return tableSplit
    
    @staticmethod
    def mergeAndTOC(coverPath, pathContents, pathSummary, basePathResults, outputPath, reportTitle, logo):
        bookMarkNames = ["Contents of this report", "Buildings summary"] + [item.replace(basePathResults, '').replace('.pdf','') for item in os.listdir(basePathResults)]
        pdf_paths = [pathContents, pathSummary] + [basePathResults + "/" + item for item in os.listdir(basePathResults)]

        output = PdfWriter()
        cover = PdfReader(open(coverPath,'rb'))
        
        for i in range(len(cover.pages)):
            page = cover.pages[i]
            output.add_page(page)

        tocOrigin = mapOrigin
        tocFinal = tableEnd

        rowsperPage = math.ceil((tocFinal-tocOrigin)/(textHeight/2))
        tocPages = math.ceil(len(bookMarkNames)/((tocFinal-tocOrigin)/(textHeight/2)))
        pageOrigin = 3

        if(tocPages%2==0):
            pageLocation = pageOrigin+tocPages
        else:
            pageLocation = pageOrigin+1+tocPages

        for pagenum in range(tocPages):
            lowerbound = rowsperPage*pagenum
            upperbound = min(len(bookMarkNames), rowsperPage*(pagenum+1))
            y = tocOrigin

            packet = io.BytesIO()
            canvas_page = canvas.Canvas(packet, pagesize=A4, bottomup=0)
            # Text
            canvas_page.setFillColor(colors.black)
            canvas_page.setFont("Helvetica", 8)
            canvas_page.drawString(horizontalMargin*mm,(headerMargin-headerTextHeight)*mm, reportTitle)
            # Logo
            canvas_page.saveState()
            canvas_page.scale(1,-1)
            canvas_page.drawImage(logo, (210-horizontalMargin-headerLogoWidth)*mm, -(headerMargin-headerLogoPosition)*mm, width=headerLogoWidth*mm, height=-headerLogoHeight*mm)
            canvas_page.restoreState()
            # Page number
            canvas_page.setFont("Helvetica-Oblique", textHeight)
            if((pagenum+1)%2 == 0):
                canvas_page.drawString((horizontalMargin)*mm, (297-horizontalMargin*3/4)*mm, str(pageOrigin+pagenum))
            else:
                canvas_page.drawRightString((210-horizontalMargin)*mm, (297-horizontalMargin*3/4)*mm, str(pageOrigin+pagenum))
                
            # Title
            if(pagenum==0):
                canvas_page.setFillColor(colors.black)
                canvas_page.setFont("Helvetica-Bold", 14)
                canvas_page.drawString(horizontalMargin*mm,(headerMargin-sectionTitleSpacer)*mm, "Table of contents")
                canvas_page.bookmarkPage("Table of contents")
            # Links
            canvas_page.setFont("Helvetica", textHeight)

            for i in range(lowerbound, upperbound):
                existing_pdf = PdfReader(open(pdf_paths[i], "rb"))
            
                canvas_page.drawString(horizontalMargin*mm, y*mm, bookMarkNames[i])
                canvas_page.drawRightString((210-horizontalMargin)*mm, y*mm, str(pageLocation))
                y += textHeight/2
                pageLocation += len(existing_pdf.pages)


            canvas_page.save()
            #move to the beginning of the StringIO buffer   

            packet.seek(0)
            existing_pdf = PdfReader(packet)
            page = existing_pdf.pages[0]
            output.add_page(page)

        output.add_outline_item("Table of contents", 0 + len(cover.pages))

        if(tocPages%2==1):
            packet = io.BytesIO()
            canvas_page = canvas.Canvas(packet, pagesize=A4, bottomup=0)
            # Text
            canvas_page.setFillColor(colors.black)
            canvas_page.setFont("Helvetica", 8)
            canvas_page.drawString(horizontalMargin*mm,(headerMargin-headerTextHeight)*mm, reportTitle)
            # Logo
            canvas_page.saveState()
            canvas_page.scale(1,-1)
            canvas_page.drawImage(logo, (210-horizontalMargin-headerLogoWidth)*mm, -(headerMargin-headerLogoPosition)*mm, width=headerLogoWidth*mm, height=-headerLogoHeight*mm)
            canvas_page.restoreState()
            # Page number
            canvas_page.setFont("Helvetica-Oblique", textHeight)
            canvas_page.drawString((horizontalMargin)*mm, (297-horizontalMargin*3/4)*mm, str(tocPages+pageOrigin))
            
            # Export
            canvas_page.save()
            packet.seek(0)
            existing_pdf = PdfReader(packet)
            page = existing_pdf.pages[0]
            output.add_page(page)

        if(tocPages%2==0):
            pageLocation = tocPages
        else:
            pageLocation = 1+tocPages
        current_page = pageLocation

        for index, pdf_path in enumerate(pdf_paths):
            existing_pdf = PdfReader(open(pdf_path, "rb"))
            for j in range(len(existing_pdf.pages)):
                page = existing_pdf.pages[j]
                output.add_page(page)
            output.add_outline_item(bookMarkNames[index], current_page + len(cover.pages))
            current_page += len(existing_pdf.pages)

        with open(outputPath, "wb") as f:
            output.write(f)