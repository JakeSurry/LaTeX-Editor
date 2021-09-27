from pdf2image import convert_from_path
import subprocess

r = subprocess.run(['/Library/TeX/texbin/pdflatex', '-output-format=pdf', '-interaction=nonstopmode', 'latex_raw.TeX'], cwd='latex_output', capture_output = True)

images = convert_from_path('latex_output/latex_raw.pdf')

for image in images:
    image.save('out.jpg', 'JPEG')
