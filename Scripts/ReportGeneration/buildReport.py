import os
from tqdm import tqdm
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
import json
import pandas as pd
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "70_el Besòs i el Maresme"
neighborhood = "HECAPO"
# neighborhood = "Test_70_el Besòs i el Maresme"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

import warnings
warnings.filterwarnings('ignore')

def generate_first_page(c, parcel, construction, reportFolder, images):
    page_width, page_height = A4
    margin_top = 20 * mm
    margin_side = 20 * mm

    # Add title
    title = f"{parcel} - {construction}"
    c.setFont("Helvetica-Bold", 14)
    title_width = c.stringWidth(title, "Helvetica-Bold", 14)
    c.drawString((page_width - title_width) / 2, page_height - margin_top, title)
    
        # Add horizontal line
    line_y = page_height - margin_top - 10  # Slightly below the title
    c.setLineWidth(2)
    c.line(margin_side, line_y, page_width - margin_side, line_y)
    
     # Add location information heading with bullet
    location_title =  '\t ' + "Location information"  # Bullet point with text
    c.setFont("Helvetica-BoldOblique", 12)
    c.drawString(margin_side, line_y - 30, location_title)
        # Add horizontal line below the heading
    heading_line_y = line_y - 35
    c.setLineWidth(1)
    c.line(margin_side, heading_line_y, page_width - margin_side, heading_line_y)
        # Add images and text below the line
    images_location = images[0:3]
    image_width = 55 * mm  # Width for each image
    image_height = 55 * mm  # Height for each image
    spacing = 2.5 * mm  # Spacing between images
    image_y = heading_line_y - spacing - image_height
    
    c.setFont("Helvetica", 10)
    for idx, image in enumerate(images_location):
        x_pos = margin_side + idx * (image_width + spacing)
        c.drawImage(image["path"], x_pos, image_y, image_width, image_height, preserveAspectRatio=True, anchor='c')
        title_width = c.stringWidth(image["caption"])
        c.drawCentredString(x_pos + (title_width / 2), image_y - 2*spacing, image["caption"])

     # Add rooftop identification heading with bullet
    rooftops_title =  '\t ' +  "Identified rooftops"  # Bullet point with text
    c.setFont("Helvetica-BoldOblique", 12)
    c.drawString(margin_side, image_y - 30 - spacing, rooftops_title)
         # Add horizontal line below the heading
    rooftops_heading_y = image_y - 35 - spacing
    c.line(margin_side, rooftops_heading_y, page_width - margin_side, rooftops_heading_y)
        # Add image on the left
    rooftop_image_path = images[3]["path"]  # Path to the image
    rooftop_image_width = 80 * mm  # Image width
    rooftop_image_height = 80 * mm  # Image height
    rooftop_image_x = margin_side  # Position on the left
    rooftop_image_y = rooftops_heading_y - rooftop_image_height - 10

    c.drawImage(
        rooftop_image_path,
        rooftop_image_x,
        rooftop_image_y,
        rooftop_image_width,
        rooftop_image_height,
        preserveAspectRatio=True,
        anchor="c",
    )
    # Add table
    planeIDdf = pd.read_csv(reportFolder + "PlaneID.csv")
    # filtered_columns = [col for col in planeIDdf.columns if not col.lower().startswith("color")]
    filtered_columns  = ["ID","area","tilt","azimuth","centroidHeight", "silhouette"]
    filtered_data = planeIDdf[filtered_columns]
    for field in ["area", "tilt", "azimuth", "centroidHeight", "silhouette"]:
        filtered_data.loc[:,field] = filtered_data[field].apply(lambda x: f"{x:.2f}")
    filtered_columns = filtered_columns[0:1] + [""] + filtered_columns[1:]  # Insert an empty column at the start
    table_data = [filtered_columns] + filtered_data.values.tolist()
    # table_data =  [filtered_columns]  + [[""] + row.tolist() for row in filtered_data.values]  # Add empty column for each row
    titles = ["Plane", "", "Area", "Tilt", "Azimuth", "Height at", "Confidence"]
    units = ["", "", "(m²)", "(º)", "(º)", "center (m)", ""]
    table_data = [titles] + [units] + [[""] + row.tolist() for row in filtered_data.values] 
    
    filtered_columns[filtered_columns.index("ID")] = "Plane"
    filtered_columns[filtered_columns.index("area")] = "Area (m²)"
    filtered_columns[filtered_columns.index("tilt")] = "Tilt (º)"
    filtered_columns[filtered_columns.index("azimuth")] = "Azimuth (º)"
    filtered_columns[filtered_columns.index("silhouette")] = "Confidence"
    filtered_columns[filtered_columns.index("centroidHeight")] = "Center height (m)"

        # Define table position and size
    table_x = margin_side + 77.5 * mm  # Positioned to the right of the image
    table_y = rooftops_heading_y - 10  # Below the heading
    table_width = page_width - table_x - margin_side  # Adjust width to fit within margins
    table = Table(table_data, colWidths=[5*mm, 5*mm, 15*mm, 12*mm, 17*mm, 18*mm, 21*mm])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.white),  # Header background
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),       # Header text color
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),              # Center align all cells
            ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),    # Bold font for header
            ("FONTSIZE", (0, 0), (-1, -1), 9),                  # Font size for all cells
            # ("FONTSIZE", (0, 0), (-1, 1), 9),   
            ('LINEBELOW', (0, 1), (-1, 1), 1, colors.black),
            # ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ])
    )

    table.setStyle(
        TableStyle([
            ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),   
           ])
    )

        # Align "Plane" (left) and other columns (right)
    for col_idx, column_name in enumerate(filtered_columns):
        if column_name == "Plane":
            table.setStyle([("ALIGN", (col_idx, 0), (col_idx, -1), "LEFT")])  # Align "Plane" to the left
        else:
            table.setStyle([("ALIGN", (col_idx, 0), (col_idx, -1), "RIGHT")])  # Align all other columns to the right
    table.setStyle([("ALIGN", (0, 0), (0, -1), "LEFT")]) 

        # Add alternating row colors for body rows
    for row_idx in range(1, len(table_data)):  # Start from the first data row
        bg_color = colors.whitesmoke if row_idx % 2 == 0 else colors.white
        table.setStyle([("BACKGROUND", (0, row_idx), (-1, row_idx), bg_color)])

    for row_idx in range(len(planeIDdf)):  # Skip header row
        color = (
            (planeIDdf["colorR"][row_idx]),
            (planeIDdf["colorG"][row_idx]),
            (planeIDdf["colorB"][row_idx]),
            # (planeIDdf["colorAlpha"][row_idx])
        ) 
        color = colors.toColor(color)
        color.alpha = planeIDdf["colorAlpha"][row_idx]
        # Set the background color for the new column (empty column)
        table.setStyle([("BACKGROUND", (0, row_idx + 2), (0, row_idx + 2), color)])

        # Calculate vertical centering
    table_height = len(table_data) * 8  # Approximate table height (rows * font size)
    content_center_y = rooftops_heading_y - rooftop_image_height / 2 + 10*mm # Center of the image
    table_start_y = content_center_y + table_height / 2  # Align table center with image center

    table.wrapOn(c, table_x, table_start_y)
    table.drawOn(c, table_x, table_start_y - table._height)

     # Add radiation information heading with bullet
    radiation_title = '\t ' + "Radiation summary"  # Bullet point with text
    c.setFont("Helvetica-BoldOblique", 12)
    c.drawString(margin_side, rooftop_image_y - 10 - spacing, radiation_title)
         # Add horizontal line below the heading
    radiation_heading_y = rooftop_image_y - 15 - spacing
    c.line(margin_side, radiation_heading_y, page_width - margin_side, radiation_heading_y)
        # Add image on the left
    radiation_image_path = images[4]["path"]  # Path to the image
    radiation_image_width = 80 * mm  # Image width
    radiation_image_height = 80 * mm  # Image height
    radiation_image_x = margin_side  # Position on the left
    radiation_image_y = radiation_heading_y - radiation_image_height - 10

    c.drawImage(
        radiation_image_path,
        radiation_image_x,
        radiation_image_y,
        radiation_image_width,
        radiation_image_height,
        preserveAspectRatio=True,
        anchor="c",
    )

    # Add table
    poaDF = pd.read_csv(reportFolder + "PoA.csv")
    poaDF["Area"] = poaDF["Area"].apply(lambda x: f"{x:.1f}")
    filtered_columns = [col for col in poaDF.columns if not col.lower().startswith("color")]
    filtered_data = poaDF[filtered_columns]

    filtered_columns = [""] + filtered_columns  # Insert an empty column at the start
    table_data = [filtered_columns] + filtered_data.values.tolist()

    filtered_columns[filtered_columns.index("Range")] = "Plane of Array radiation"
    filtered_columns[filtered_columns.index("Area")] = "Area"

    units = ["", "(kWh/m²/year)", "(m²)"]
    table_data =  [filtered_columns]  + [units] + [[""] + row.tolist() for row in filtered_data.values]  # Add empty column for each row


        # Define table position and size
    table_x = margin_side + 85*mm + (page_width - 85*mm - 2*margin_side - 60*mm)/2  # Positioned to the right of the image
    table_y = radiation_heading_y- 5*mm # Below the heading
    table_width = page_width - table_x - margin_side  # Adjust width to fit within margins
    table = Table(table_data, colWidths=[5 * mm, 35 * mm, 20 * mm])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.white),  # Header background
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),       # Header text color
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),              # Center align all cells
            ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),    # Bold font for header
            ("FONTSIZE", (0, 0), (-1, -1), 9),                  # Font size for all cells
            ('LINEBELOW', (0, 1), (-1, 1), 1, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ])
    )

    table.setStyle(
        TableStyle([
            ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),   
           ])
    )

      # Align "Plane" (left) and other columns (right)
    for col_idx, column_name in enumerate(filtered_columns):
        if column_name == "Area":
            table.setStyle([("ALIGN", (col_idx, 0), (col_idx, -1), "RIGHT")])  # Align "Plane" to the left

         # Add alternating row colors for body rows
    for row_idx in range(1, len(table_data)):  # Start from the first data row
        bg_color = colors.whitesmoke if row_idx % 2 == 0 else colors.white
        table.setStyle([("BACKGROUND", (0, row_idx), (-1, row_idx), bg_color)])

    for row_idx in range(len(poaDF)):  # Skip header row
        color = (
            (poaDF["colorR"][row_idx]),
            (poaDF["colorG"][row_idx]),
            (poaDF["colorB"][row_idx]),
            # (planeIDdf["colorAlpha"][row_idx])
        ) 
        color = colors.toColor(color)
        color.alpha = poaDF["colorAlpha"][row_idx]
        # Set the background color for the new column (empty column)
        table.setStyle([("BACKGROUND", (0, row_idx + 2), (0, row_idx + 2), color)])

    table.wrapOn(c, table_x, table_y)
    table.drawOn(c, table_x, table_y - table._height)

    return c

def generate_second_page(c, parcel, construction, reportFolder, images):
    page_width, page_height = A4
    margin_top = 25 * mm
    margin_side = 20 * mm

     # Add location information heading with bullet
    location_title =  '\t ' + "PV production detail"  # Bullet point with text
    c.setFont("Helvetica-BoldOblique", 12)
    line_y = page_height - margin_top - 10  # Slightly below the title
    c.drawString(margin_side, line_y - 30, location_title)
    heading_line_y = line_y - 35
    c.setLineWidth(1)
    c.line(margin_side, heading_line_y, page_width - margin_side, heading_line_y)

    # Add image on the left
    image_path = images[5]["path"]  # Path to the image
    image_width = 100 * mm  # Image width
    image_height = 100 * mm  # Image height
    image_x = (page_width - image_width) / 2  # Position on the left
    image_y = heading_line_y - image_height - 10

    c.drawImage(
        image_path,
        image_x,
        image_y,
        image_width,
        image_height,
        preserveAspectRatio=True,
        anchor="c",
    )

    pvPanelsDF = pd.read_csv(reportFolder + "PVpanels.csv")
    pvPanelsDF = pvPanelsDF[["plane","category","panel_count", "yearly_total"]]

    totals = pvPanelsDF.groupby('plane', as_index=False).agg({
        'category': lambda x: 'Total',  # Mark the category as "Total"
        'panel_count': 'sum',          # Sum panel_count
        'yearly_total': 'sum'          # Sum yearly_total
    })
    resultDF = pd.concat([pvPanelsDF, totals], ignore_index=True).sort_values(by=['plane', 'category'])
    resultDF["yearly_total"] = resultDF["yearly_total"].apply(lambda x: "{:.3f}".format(x/1000.0))
    resultDF.reset_index(drop=True, inplace=True)
    resultDF['plane'] = resultDF['plane'].astype(str)  # Ensure the column is a string for replacement
    resultDF['plane'] = resultDF['plane'].where(resultDF['plane'] != resultDF['plane'].shift(), "")
    
    filtered_columns = resultDF.columns
    columns = ["Plane", "PV DC Generation", "Panels", "Total PV Generation"]
    units = ["", "(kWh/panel/year)", "placed", "(MWh/year)"]
    table_data = [columns] + [units] + resultDF.values.tolist()

    table_x = (page_width - 110*mm) / 2  # Positioned to the right of the image
    table_y = image_y - 10  # Below the image
    table_width = page_width - table_x - margin_side  # Adjust width to fit within margins
    table = Table(table_data, colWidths=[15*mm, 40*mm, 15*mm, 40*mm])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.white),  # Header background
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),       # Header text color
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),              # Right align all cells
            ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),    # Bold font for header
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),    # Bold font for header
            ("FONTSIZE", (0, 0), (-1, -1), 9),                  # Font size for all cells
            ('LINEBELOW', (0, 1), (-1, 1), 1, colors.black),
            # ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ])
    )

    for col_idx, column_name in enumerate(filtered_columns):
        if column_name == "Plane":
            table.setStyle([("ALIGN", (col_idx, 0), (col_idx, -1), "CENTER")])  # Align "Plane" to the left
        elif column_name == "category":
            table.setStyle([("ALIGN", (col_idx, 0), (col_idx, -1), "LEFT")])  # Align all other columns to the right
    table.setStyle([("ALIGN", (0, 0), (0, 0), "LEFT")])
    table.setStyle([("ALIGN", (0, 1), (0, -1), "CENTER")])  # Align "Plane" to the left

    totals_indices = [idx for idx, row in enumerate(table_data[2:], start=2) if "Total" in row]
    for total_idx in totals_indices:
        table.setStyle([
        ("FONTNAME", (0, total_idx), (-1, total_idx), "Helvetica-Bold"),  # Bold font for totals
        ("LINEBELOW", (0, total_idx), (-1, total_idx), 1, colors.black),  # Line below totals
    ])

    table.wrapOn(c, table_x, table_y)
    table.drawOn(c, table_x, table_y - table._height)

    return c

    

def generate_pdf(parcel, construction, reportFolder, images, output_folder):
    # File path
    pdf_file = os.path.join(output_folder, parcel + "_" + construction + "_Report.pdf")
    
    # Page settings
    page_width, page_height = A4
    margin_top = 25 * mm
    margin_side = 20 * mm
    
    try:
        # Create canvas
        c = canvas.Canvas(pdf_file, pagesize=A4)
        
        c = generate_first_page(c, parcel, construction, reportFolder, images)

        # Save first page and add a second page
        c.showPage()    
        c = generate_second_page(c, parcel, construction, reportFolder, images)

        # Finalize the PDF
        c.save()
    except Exception as e:
        print(e)

for parcel in tqdm(os.listdir(parcelsFolder), desc="Parcels", leave=True):
    # if(parcel == "4054901DF3845C"):   
        parcelSubfolder = parcelsFolder + parcel + "/"
        for construction in tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)],  desc="Constructions", leave=False):
            # if(construction == "408"):
                constructionFolder = parcelSubfolder + construction + "/"
                reportFolder = constructionFolder + "Report Files/"

                # Prepare location data
                with open(reportFolder + 'location_info.json') as f:
                    location_info = json.load(f)

                caption1 = "{:.5f}".format(location_info["latitude"]) + " N, " + "{:.5f}".format(location_info["longitude"]) + " E"
                caption2 = "Building area {:.2f} m²".format(location_info["area"])
                caption3 = "{:.0f} LiDAR points ({:.1f} points/m²)".format(location_info["lidarPoints"], location_info["density"])
                images = [
                    {"path": constructionFolder + "Report Files/ZoomOut_Scaled.png", "caption": caption1},
                    {"path": constructionFolder + "Report Files/ZoomIn.png", "caption": caption2},
                    {"path": constructionFolder + "Report Files/LiDAR.png", "caption": caption3},
                    {"path": constructionFolder + "Report Files/PlaneID.png"},
                    {"path": constructionFolder + "Report Files/PoA.png"},
                    {"path": constructionFolder + "Report Files/PVpanels.png"}
                ]

                # output_folder = "/home/jaumeasensio/Documents/TFM_Web/jaumeasensiob.github.io/data/Reports/"
                output_folder = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/" + neighborhood  + "/Reports/"
                generate_pdf(parcel, construction, reportFolder, images, output_folder)