from flask import Flask, request, send_from_directory, render_template_string
import os
import subprocess
from werkzeug.utils import secure_filename
import uuid
import logging

UPLOAD_FOLDER = "/tmp/uploads"
ALLOWED_EXTENSIONS = {"docx"}

# Garante que o diretório existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Logging simples para ver via kubectl logs
logging.basicConfig(level=logging.INFO)

HTML = """
<!doctype html>
<html lang="pt-br">
  <head>
    <meta charset="utf-8">
    <title>Conversor Word para PDF</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  </head>
  <body class="bg-light">
    <div class="container py-5">
      <h2 class="mb-4 text-center">Conversor de arquivos .docx para PDF</h2>
      <form method="post" enctype="multipart/form-data" class="text-center">
        <div class="mb-3">
          <input class="form-control" type="file" name="file" required>
        </div>
        <button type="submit" class="btn btn-primary">Converter</button>
      </form>

      {% if filename %}
        <div class="alert alert-success mt-4 text-center">
          <strong>PDF gerado com sucesso!</strong><br>
          <a href="/download/{{ filename }}" class="btn btn-success mt-2">Clique aqui para baixar</a>
        </div>
      {% endif %}
    </div>
  </body>
</html>
"""

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template_string(HTML, filename=None)
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return render_template_string(HTML, filename=None)

        filename = secure_filename(file.filename)
        unique_id = uuid.uuid4().hex
        unique_filename = f"{unique_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        try:
            subprocess.run([
                "libreoffice", "--headless", "--convert-to", "pdf",
                "--outdir", app.config['UPLOAD_FOLDER'],
                filepath
            ], check=True)
        except subprocess.CalledProcessError as e:
            logging.error("Erro ao converter PDF: %s", e)
            return "Erro ao converter o arquivo", 500

        pdf_filename = unique_filename.rsplit('.', 1)[0] + ".pdf"
        logging.info("PDF gerado: %s", pdf_filename)
        return render_template_string(HTML, filename=pdf_filename)

    return render_template_string(HTML, filename=None)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
