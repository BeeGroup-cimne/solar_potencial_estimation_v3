import os
from ReportTemplates.CanvasWriter import CanvasWriter
from ReportTemplates.DataManager import DataManager
from pypdf import PdfMerger

from PyPDF2 import PdfWriter, PdfReader 
import io
import math

class ReportTypes():

    def __init__(self, reportTitle, logo, initialPage,  resultsPath, mapResultsPath, numberPages=True):
        self.reportTitle = reportTitle
        self.logo = logo
        self.pagenumber = initialPage
        self.resultsPath = resultsPath
        self.mapResultsPath = mapResultsPath
        self.numberPages = numberPages
    
    def updateData(self, planeListPath, sunSimulationPath, planedf, fields, planePointList):
        self.planeListPath = planeListPath
        self.sunSimulationPath = sunSimulationPath
        self.planedf = planedf
        self.fields = fields
        self.planePointList = planePointList
    
    def normal_file(self, title, building):
        buildingName = building.identifier.values[0]

        # Front Page
        
        c = CanvasWriter("PDF docs/Construction/" + title + ("_FrontPage.pdf"))
        c.set_header(self.reportTitle, self.logo)
        c.set_title(title)
        mapPath = self.mapResultsPath + "/" + buildingName + "_ZoomOut.png"
        satPath = self.mapResultsPath + "/" + buildingName + "_ZoomIn.png"
        LiDARPath = self.mapResultsPath + "/" +  buildingName + "_LiDAR.png"

        cadastrePath = self.resultsPath + buildingName + "/01 - Segmented Buildings/" + buildingName + ".gpkg"
        pointCloudPath = self.resultsPath + buildingName + "/01 - Segmented Buildings/" + buildingName + ".csv"
        if(os.path.isfile(cadastrePath)):
            if(os.path.isfile(pointCloudPath)):
                if(os.stat(pointCloudPath).st_size != 0):
                    # direction = building.Region.values[0] + ", " + building.Municipality.values[0] + ", " +  building.Road.values[0] + " " +  building["Road number"].values[0]
                    direction = building.Name.values[0] + ", " +  building.Road.values[0] + " " +  building["Road number"].values[0] + ", " + building.Municipality.values[0] + ", " +   building.Owner.values[0]
                    c.mapSection(mapPath, satPath, LiDARPath, building.lat.values[0], building.long.values[0], direction, cadastrePath, pointCloudPath)

        if(os.path.isfile(self.planeListPath)):
            planeFigPath = self.mapResultsPath + "/" + buildingName + "_Planes.png"
            c.planeSection(self.planedf, self.fields, self.planePointList, planeFigPath)

            if(os.path.isfile(self.sunSimulationPath)):
                sundf = DataManager.prepare_sundf(self.sunSimulationPath)
                summaryEnergydf = DataManager.prepare_summaryEnergydf(sundf)
                sunByRoofList = DataManager.prepare_sunByRoofList(sundf)

                heatmapFigPath = self.mapResultsPath + "/" + buildingName + "_EnergyDensity.png"
                c.energySummarySection(heatmapFigPath, summaryEnergydf)
        if(self.numberPages):
            c.writePageNumber(self.pagenumber)
            self.pagenumber = self.pagenumber + 1
        c.canvas_page.save()

        # BackPage
        
        c = CanvasWriter("PDF docs/Construction/" + title + ("_BackPage.pdf"))
        c.set_header(self.reportTitle, self.logo)
        if(os.path.isfile(self.sunSimulationPath)):
            heatmapPlanesFigPath = self.mapResultsPath + "/" + buildingName + "_EnergyNumbered.png"
            
            # sundf = DataManager.prepare_sundf(self.sunSimulationPath)
            # summaryEnergydf = DataManager.prepare_summaryEnergydf(sundf)
            # sunByRoofList = DataManager.prepare_sunByRoofList(sundf)

            leftdf, rightdf = DataManager.splitList(sunByRoofList, large=False)
            c.energyDetailSection(heatmapPlanesFigPath, leftdf, rightdf)

        if(self.numberPages):
            c.writePageNumber(self.pagenumber)
            self.pagenumber = self.pagenumber + 1
        c.canvas_page.save()

        # Merge
        pdfs = ["PDF docs/Construction/" + title + '_FrontPage.pdf', "PDF docs/Construction/" + title + '_BackPage.pdf']
        merger = PdfMerger()
        for pdf in pdfs:
            merger.append(pdf)
        merger.write("PDF docs/" + title + ".pdf")
        merger.close()
    
    def large_file(self, title, building):
        buildingName = building.identifier.values[0]

        # Plane Page
        
        c = CanvasWriter("PDF docs/Construction/" + title + ("_PlanePage.pdf"))
        c.set_header(self.reportTitle, self.logo)
        c.set_title(title)
        mapPath = self.mapResultsPath + "/" + buildingName + "_ZoomOut.png"
        satPath = self.mapResultsPath + "/" + buildingName + "_ZoomIn.png"
        LiDARPath = self.mapResultsPath + "/" +  buildingName + "_LiDAR.png"

        cadastrePath = self.resultsPath + buildingName + "/01 - Segmented Buildings/" + buildingName + ".gpkg"
        pointCloudPath = self.resultsPath + buildingName + "/01 - Segmented Buildings/" + buildingName + ".csv"
        if(os.path.isfile(cadastrePath)):
            if(os.path.isfile(pointCloudPath)):
                if(os.stat(pointCloudPath).st_size != 0):
                    # direction = building.Region.values[0] + ", " + building.Municipality.values[0] + ", " +  building.Road.values[0] + " " +  building["Road number"].values[0]
                    direction = building.Name.values[0] + ", " +  building.Road.values[0] + " " +  building["Road number"].values[0] + ", " + building.Municipality.values[0] + ", " +   building.Owner.values[0]
                    c.mapSection(mapPath, satPath, LiDARPath, building.lat.values[0], building.long.values[0], direction, cadastrePath, pointCloudPath)

        if(os.path.isfile(self.planeListPath)):
            planeFigPath = self.mapResultsPath + "/" + buildingName + "_Planes.png"
            c.planeSectionLarge(self.planedf, self.fields, self.planePointList, planeFigPath)
        
        if(self.numberPages):
            c.writePageNumber(self.pagenumber)
            self.pagenumber = self.pagenumber + 1
        
        c.canvas_page.save()

        # Sun Summary page
        c = CanvasWriter("PDF docs/Construction/" + title + ("_SunSummaryPage.pdf"))

        if(os.path.isfile(self.sunSimulationPath)):
            heatmapFigPath = self.mapResultsPath + "/" + buildingName + "_EnergyDensity.png"
            sundf = DataManager.prepare_sundf(self.sunSimulationPath)
            summaryEnergydf = DataManager.prepare_summaryEnergydf(sundf)
            sunByRoofList = DataManager.prepare_sunByRoofList(sundf)
            c.energySummarySectionLarge(heatmapFigPath, summaryEnergydf)

        if(self.numberPages):
            c.writePageNumber(self.pagenumber)
            self.pagenumber = self.pagenumber + 1
        
        c.canvas_page.save()

        # SunDetail Front Page
        c = CanvasWriter("PDF docs/Construction/" + title + "_DetailFrontPage.pdf")
        c.set_header(self.reportTitle, self.logo)
        if(os.path.isfile(self.sunSimulationPath)):
            heatmapPlanesFigPath = self.mapResultsPath + "/" + buildingName + "_EnergyNumbered.png"
            
            # sundf = DataManager.prepare_sundf(self.sunSimulationPath)
            # summaryEnergydf = DataManager.prepare_summaryEnergydf(sundf)
            # sunByRoofList = DataManager.prepare_sunByRoofList(sundf)

            left1df, right1df, left2df, right2df = DataManager.splitList(sunByRoofList, large=True)

            c.energyDetailSectionLarge(heatmapPlanesFigPath, left1df, right1df, "(1/2)")

        if(self.numberPages):
            c.writePageNumber(self.pagenumber)
            self.pagenumber = self.pagenumber + 1
        
        c.canvas_page.save()

        # SunDetail Back Page
        c = CanvasWriter("PDF docs/Construction/" + title + "_DetailBackPage.pdf")
        c.set_header(self.reportTitle, self.logo)
        if(os.path.isfile(self.sunSimulationPath)):
            heatmapPlanesFigPath = self.mapResultsPath + "/" + buildingName + "_EnergyNumbered.png"
            c.energyDetailSectionLarge(heatmapPlanesFigPath, left2df, right2df, "(2/2)")

        if(self.numberPages):
            c.writePageNumber(self.pagenumber)
            self.pagenumber = self.pagenumber + 1
        
        c.canvas_page.save()

        # Merge
        pdfs = ["PDF docs/Construction/" + title + '_PlanePage.pdf', "PDF docs/Construction/" + title + '_SunSummaryPage.pdf', 
                "PDF docs/Construction/" + title + '_DetailFrontPage.pdf', "PDF docs/Construction/" + title + '_DetailBackPage.pdf']
        merger = PdfMerger()
        for pdf in pdfs:
            merger.append(pdf)
        merger.write("PDF docs/" + title + ".pdf")
        merger.close()
    
    def notSimulated_file(self, title, building):
        # Front Page
        buildingName = building.identifier.values[0]
        
        c = CanvasWriter("PDF docs/" + title + (".pdf"))
        c.set_header(self.reportTitle, self.logo)
        c.set_title(title)
        mapPath = self.mapResultsPath + "/" + buildingName + "_ZoomOut.png"
        satPath = self.mapResultsPath + "/" + buildingName + "_ZoomIn.png"
        LiDARPath = self.mapResultsPath + "/" +  buildingName + "_LiDAR.png"

        cadastrePath = self.resultsPath + buildingName + "/01 - Segmented Buildings/" + buildingName + ".gpkg"
        pointCloudPath = self.resultsPath + buildingName + "/01 - Segmented Buildings/" + buildingName + ".csv"
        if(os.path.isfile(cadastrePath)):
            if(os.path.isfile(pointCloudPath)):
                if(os.stat(pointCloudPath).st_size != 0):
                    # direction = building.Region.values[0] + ", " + building.Municipality.values[0] + ", " +  building.Road.values[0] + " " +  building["Road number"].values[0]
                    direction = building.Name.values[0] + ", " +  building.Road.values[0] + " " +  building["Road number"].values[0] + ", " + building.Municipality.values[0] + ", " +   building.Owner.values[0]
                    c.mapSection(mapPath, satPath, LiDARPath, building.lat.values[0], building.long.values[0], direction, cadastrePath, pointCloudPath)
            
                else:
                    # direction = building.Region.values[0] + ", " + building.Municipality.values[0] + ", " +  building.Road.values[0] + " " +  building["Road number"].values[0]
                    direction = building.Name.values[0] + ", " +  building.Road.values[0] + " " +  building["Road number"].values[0] + ", " + building.Municipality.values[0] + ", " +   building.Owner.values[0]
                    c.mapSectionEmpty(mapPath, satPath, building.lat.values[0], building.long.values[0], direction)
        
        c.badQualityLabel()

        if(self.numberPages):
            c.writePageNumber(self.pagenumber)
            self.pagenumber = self.pagenumber + 1
        
        c.canvas_page.save()

    def summaryReport(self, summaryTabledf, destinationPath):

        tableSplit = CanvasWriter.split_table(summaryTabledf)

        packet = io.BytesIO()
        page = CanvasWriter(packet)
        page.set_header(self.reportTitle, self.logo)
        page.set_title("Buildings summary")
        page.writeBuildingTable(tableSplit[0], x=10)
        page.writePageNumber(self.pagenumber)
        self.pagenumber = self.pagenumber +1
        page.canvas_page.save()

        #move to the beginning of the StringIO buffer   
        packet.seek(0)
        # create a new PDF with Reportlab
        new_pdf = PdfReader(packet)

        output = PdfWriter()
        output.add_page(new_pdf.pages[0])

        for i in range(1, len(tableSplit)):
            packet = io.BytesIO()
            pageN = CanvasWriter(packet)
            pageN.set_header(self.reportTitle, self.logo)
            pageN.writeBuildingTable(tableSplit[i], x=10)
            pageN.writePageNumber(self.pagenumber)
            self.pagenumber = self.pagenumber +1
            pageN.canvas_page.save()

            packet.seek(0)
            new_pdf = PdfReader(packet)
            output.add_page(new_pdf.pages[0])

        output_stream = open(destinationPath, "wb")
        output.write(output_stream)
        output_stream.close()