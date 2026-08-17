import io
import os
import subprocess
import tempfile
from flask import Flask, render_template, request, send_file
from pypdf import PdfMerger, PdfReader, PdfWriter
from PIL import Image

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

ALLOWED_OFFICE_EXTENSIONS = {
    '.doc', '.docx', '.odt', '.rtf', '.txt',
    '.xls', '.xlsx', '.ods', '.csv',
    '.ppt', '.pptx', '.odp'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge', methods=['POST'])
def merge_pdfs():
    files = request.files.getlist('pdf_files')
    if not files or len(files) < 2:
        return "Debes subir al menos 2 archivos PDF.", 400
    merger = PdfMerger()
    for file in files:
        merger.append(file)
    output = io.BytesIO()
    merger.write(output)
    merger.close()
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="unido.pdf", mimetype='application/pdf')

@app.route('/split', methods=['POST'])
def split_pdf():
    file = request.files.get('pdf_file')
    page_start = int(request.form.get('start', 1)) - 1
    page_end = int(request.form.get('end', 1))
    reader = PdfReader(file)
    writer = PdfWriter()
    for i in range(page_start, min(page_end, len(reader.pages))):
        writer.add_page(reader.pages[i])
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="extraido.pdf", mimetype='application/pdf')

@app.route('/protect', methods=['POST'])
def protect_pdf():
    file = request.files.get('pdf_file')
    password = request.form.get('password')
    reader = PdfReader(file)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="protegido.pdf", mimetype='application/pdf')

@app.route('/img2pdf', methods=['POST'])
def img_to_pdf():
    images = request.files.getlist('images')
    if not images:
        return "Sube al menos una imagen", 400
    img_list = []
    for img_file in images:
        img = Image.open(img_file).convert('RGB')
        img_list.append(img)
    output = io.BytesIO()
    img_list[0].save(output, format='PDF', save_all=True, append_images=img_list[1:])
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="convertido.pdf", mimetype='application/pdf')

@app.route('/office2pdf', methods=['POST'])
def office_to_pdf():
    file = request.files.get('doc_file')
    if not file or not file.filename:
        return "No se envió ningún archivo.", 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_OFFICE_EXTENSIONS:
        return f"Formato no soportado ({ext}).", 400

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, file.filename)
        file.save(input_path)

        cmd = [
            'soffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', tmpdir,
            input_path
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            return "Error convirtiendo el documento.", 500

        base_name = os.path.splitext(file.filename)[0]
        output_pdf = os.path.join(tmpdir, f"{base_name}.pdf")

        if os.path.exists(output_pdf):
            with open(output_pdf, 'rb') as f:
                pdf_data = io.BytesIO(f.read())
            pdf_data.seek(0)
            return send_file(pdf_data, as_attachment=True, download_name=f"{base_name}.pdf", mimetype='application/pdf')
        else:
            return "No se pudo generar el PDF.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)