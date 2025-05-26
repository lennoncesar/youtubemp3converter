from flask import Flask, request, send_file, jsonify, render_template_string
from yt_dlp import YoutubeDL
import os
import re
from pathlib import Path

app = Flask(__name__)
DOWNLOAD_FOLDER = str(Path.home() / "Downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def sanitize_filename(name):
    # Remove caracteres inválidos para nomes de arquivos
    return re.sub(r'[\\/*?:"<>|]', "", name)

@app.route('/')
def home():
    with open('index.html', encoding='utf-8') as f:
    return render_template_string(f.read())

@app.route('/convert', methods=['POST'])
def convert():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL não fornecida'}), 400

    # Extrair informações do vídeo sem fazer o download
    ydl_opts_info = {'quiet': True}
    with YoutubeDL(ydl_opts_info) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'audio')
        except Exception as e:
            return jsonify({'error': f'Erro ao extrair informações do vídeo: {str(e)}'}), 500

    # Sanitizar o título para uso como nome de arquivo
    safe_title = sanitize_filename(title)
    output_path = os.path.join(DOWNLOAD_FOLDER, safe_title)

    # Configurar opções para download e conversão
    ydl_opts_download = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            {
                'key': 'FFmpegMetadata'
            }
        ],
        'ffmpeg_args': ['-b:a', '96k', '-ac', '2'],
        'quiet': True,
    }

    try:
        with YoutubeDL(ydl_opts_download) as ydl:
            ydl.download([url])
    except Exception as e:
        return jsonify({'error': f'Erro ao converter o vídeo: {str(e)}'}), 500

    filename = f"{safe_title}.mp3"
    return jsonify({'download_url': f'/download/{filename}', 'display_name': filename})

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='audio/mpeg'
        )
    else:
        return jsonify({'error': 'Arquivo não encontrado'}), 404

if __name__ == '__main__':
    app.run(debug=True)
