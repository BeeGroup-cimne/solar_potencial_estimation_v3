from pypdf import PdfMerger, PdfWriter
import os
import tqdm

neighborhood = "HECAPO"
reports_folder = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/" + neighborhood + "/Reports/"
pdfs = os.listdir(reports_folder)
pdfs.sort()

merger = PdfMerger()

for pdf in pdfs:
    merger.append(reports_folder + pdf)

output_file = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/" + neighborhood + "/Reports_merged_Compressed.pdf"
merger.write(output_file)
merger.close()


writer = PdfWriter(clone_from=output_file)

for page in tqdm.tqdm(writer.pages):
    for img in page.images:
        img.replace(img.image, quality=40)
    page.compress_content_streams(level=9)  # This is CPU intensive!


with open(output_file, "wb") as f:
    writer.write(f)