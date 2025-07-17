from flask import Flask, request, jsonify, send_file, render_template_string
import os
import tempfile
import json
import subprocess
import sys
from transcribe_large_audio import process_audio_file

app = Flask(__name__)

@app.route('/')
def index():
    """返回 HTML 界面"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Audio Transcript Fine-Tuner</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }
            .header { background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); color: white; padding: 30px; text-align: center; }
            .header h1 { font-size: 2.5em; margin-bottom: 10px; font-weight: 300; }
            .upload-section { background: #f8f9fa; padding: 40px; border-bottom: 2px solid #e9ecef; }
            .upload-area { border: 3px dashed #3498db; border-radius: 15px; padding: 60px; text-align: center; transition: all 0.3s ease; background: white; position: relative; }
            .upload-area:hover { border-color: #2980b9; background: #f8f9fa; }
            .upload-icon { font-size: 4em; margin-bottom: 20px; color: #3498db; }
            .upload-text { font-size: 1.3em; color: #2c3e50; margin-bottom: 15px; }
            .file-input { position: absolute; opacity: 0; width: 100%; height: 100%; cursor: pointer; }
            .file-info { display: none; background: #d5f4e6; border: 2px solid #27ae60; border-radius: 10px; padding: 20px; margin-top: 20px; text-align: center; }
            .file-info.show { display: block; }
            .file-name { font-size: 1.2em; color: #27ae60; margin-bottom: 10px; }
            .generate-btn { background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); color: white; border: none; padding: 20px 50px; font-size: 1.3em; border-radius: 50px; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 10px 30px rgba(0, 184, 148, 0.3); display: none; margin: 20px auto; }
            .generate-btn:hover { transform: translateY(-3px); box-shadow: 0 15px 40px rgba(0, 184, 148, 0.4); }
            .generate-btn.show { display: block; }
            .status-message { background: #e3f2fd; border: 1px solid #2196f3; border-radius: 10px; padding: 15px; margin: 20px 40px; text-align: center; display: none; }
            .status-message.show { display: block; }
            .status-message.success { background: #e8f5e8; border-color: #4caf50; color: #2e7d32; }
            .status-message.error { background: #ffebee; border-color: #f44336; color: #c62828; }
            .results-section { display: none; padding: 40px; }
            .results-section.show { display: block; }
            .file-list { background: #f8f9fa; border-radius: 10px; padding: 20px; margin-top: 20px; }
            .file-item { display: flex; justify-content: space-between; align-items: center; padding: 15px; border-bottom: 1px solid #e9ecef; background: white; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .file-info-left { display: flex; align-items: center; gap: 15px; }
            .file-icon { font-size: 2em; color: #3498db; }
            .file-details h4 { margin: 0; color: #2c3e50; font-size: 1.1em; }
            .file-details p { margin: 5px 0 0 0; color: #7f8c8d; font-size: 0.9em; }
            .file-actions { display: flex; gap: 10px; }
            .view-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 0.9em; transition: background 0.3s ease; }
            .view-btn:hover { background: #2980b9; }
            .download-btn { background: #27ae60; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 0.9em; transition: background 0.3s ease; }
            .download-btn:hover { background: #219a52; }
            .loading { display: none; text-align: center; padding: 20px; }
            .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 10px; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.5); z-index: 1000; }
            .modal-content { background: white; margin: 3% auto; padding: 30px; border-radius: 20px; width: 90%; max-width: 900px; max-height: 85vh; overflow-y: auto; position: relative; }
            .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #e9ecef; }
            .modal-title { font-size: 1.5em; color: #2c3e50; display: flex; align-items: center; gap: 10px; }
            .close-btn { background: none; border: none; font-size: 1.8em; cursor: pointer; color: #7f8c8d; padding: 5px; }
            .close-btn:hover { color: #e74c3c; }
            .modal-textarea { width: 100%; min-height: 400px; padding: 20px; border: 2px solid #dee2e6; border-radius: 10px; font-family: 'Consolas', 'Monaco', monospace; font-size: 14px; line-height: 1.6; resize: vertical; background: #f8f9fa; }
            .modal-footer { display: flex; gap: 15px; justify-content: flex-end; margin-top: 20px; padding-top: 15px; border-top: 1px solid #e9ecef; }
            .modal-btn { padding: 12px 25px; border: none; border-radius: 8px; cursor: pointer; font-size: 1em; transition: all 0.3s ease; }
            .modal-btn.download { background: #27ae60; color: white; }
            .modal-btn.download:hover { background: #219a52; }
            .modal-btn.secondary { background: #95a5a6; color: white; }
            .modal-btn.secondary:hover { background: #7f8c8d; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎙️ Audio Transcript Fine-Tuner</h1>
                <p>使用 GPT-4.1 優化您的音頻轉錄內容</p>
            </div>

            <div class="upload-section">
                <div class="upload-area" id="uploadArea">
                    <input type="file" class="file-input" id="fileInput" accept="audio/*">
                    <div class="upload-icon">🎵</div>
                    <div class="upload-text">選擇音頻文件</div>
                </div>
                <div class="file-info" id="fileInfo">
                    <div class="file-name" id="fileName"></div>
                    <div class="file-size" id="fileSize"></div>
                </div>
            </div>

            <div style="text-align: center; padding: 20px;">
                <button class="generate-btn" id="generateBtn" onclick="processAudio()">
                    🚀 開始轉錄並生成改善版本
                </button>
            </div>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>正在處理您的音頻文件...</p>
            </div>

            <div class="status-message" id="statusMessage"></div>

            <div class="results-section" id="resultsSection">
                <h3>📁 輸出文件</h3>
                <div class="file-list" id="fileList"></div>
            </div>
        </div>

        <div class="modal" id="fileModal">
            <div class="modal-content">
                <div class="modal-header">
                    <div class="modal-title" id="modalTitle">📄 文件內容</div>
                    <button class="close-btn" onclick="closeModal()">&times;</button>
                </div>
                <textarea class="modal-textarea" id="modalContent" readonly></textarea>
                <div class="modal-footer">
                    <button class="modal-btn download" onclick="downloadCurrentFile()">📥 下載文件</button>
                    <button class="modal-btn secondary" onclick="closeModal()">關閉</button>
                </div>
            </div>
        </div>

        <script>
            let selectedFile = null;
            let currentFileContent = '';
            let currentFileName = '';
            let processedFiles = [];

            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const fileInfo = document.getElementById('fileInfo');
            const generateBtn = document.getElementById('generateBtn');

            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.style.borderColor = '#27ae60';
                uploadArea.style.background = '#d5f4e6';
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.style.borderColor = '#3498db';
                uploadArea.style.background = 'white';
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.style.borderColor = '#3498db';
                uploadArea.style.background = 'white';
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleFile(files[0]);
                }
            });

            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    handleFile(e.target.files[0]);
                }
            });

            function handleFile(file) {
                selectedFile = file;
                const fileSizeMB = (file.size / 1024 / 1024).toFixed(2);
                
                document.getElementById('fileName').textContent = file.name;
                document.getElementById('fileSize').textContent = `文件大小: ${fileSizeMB} MB`;
                
                fileInfo.classList.add('show');
                generateBtn.classList.add('show');
            }

            async function processAudio() {
                if (!selectedFile) {
                    showStatus('請先選擇音頻文件', 'error');
                    return;
                }

                const formData = new FormData();
                formData.append('audio', selectedFile);

                document.getElementById('loading').style.display = 'block';
                showStatus('正在處理您的音頻文件...', 'info');

                try {
                    const response = await fetch('/process_audio', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        processedFiles = result.files;
                        showStatus('處理完成！', 'success');
                        showResults();
                    } else {
                        showStatus(`錯誤: ${result.message}`, 'error');
                    }
                } catch (error) {
                    showStatus(`處理錯誤: ${error.message}`, 'error');
                } finally {
                    document.getElementById('loading').style.display = 'none';
                }
            }

            function showStatus(message, type) {
                const statusDiv = document.getElementById('statusMessage');
                statusDiv.textContent = message;
                statusDiv.className = `status-message show ${type}`;
            }

            function showResults() {
                const resultsSection = document.getElementById('resultsSection');
                const fileList = document.getElementById('fileList');
                
                const fileItems = processedFiles.map(file => `
                    <div class="file-item">
                        <div class="file-info-left">
                            <div class="file-icon">${file.type === 'No-modified' ? '📄' : '✨'}</div>
                            <div class="file-details">
                                <h4>${file.name}</h4>
                                <p>${file.type === 'No-modified' ? '原始 Whisper 轉錄' : 'GPT-4.1 改善版本'}</p>
                            </div>
                        </div>
                        <div class="file-actions">
                            <button class="view-btn" onclick="viewFile('${file.name}', '${file.type}')">
                                👁️ 查看
                            </button>
                            <button class="download-btn" onclick="downloadFile('${file.name}')">
                                📥 下載
                            </button>
                        </div>
                    </div>
                `).join('');

                fileList.innerHTML = fileItems;
                resultsSection.classList.add('show');
            }

            function viewFile(filename, type) {
                const file = processedFiles.find(f => f.name === filename);
                if (file) {
                    const modal = document.getElementById('fileModal');
                    const modalTitle = document.getElementById('modalTitle');
                    const modalContent = document.getElementById('modalContent');
                    
                    currentFileName = filename;
                    currentFileContent = file.content;
                    
                    modalTitle.innerHTML = `📄 ${filename}`;
                    modalContent.value = currentFileContent;
                    
                    modal.style.display = 'block';
                }
            }

            function closeModal() {
                document.getElementById('fileModal').style.display = 'none';
            }

            function downloadFile(filename) {
                window.location.href = `/download/${filename}`;
            }

            function downloadCurrentFile() {
                const blob = new Blob([currentFileContent], { type: 'text/markdown' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = currentFileName;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }

            window.addEventListener('click', (e) => {
                const modal = document.getElementById('fileModal');
                if (e.target === modal) {
                    closeModal();
                }
            });
        </script>
    </body>
    </html>
    """
    return html_content

@app.route('/process_audio', methods=['POST'])
def process_audio():
    """處理音頻文件"""
    try:
        if 'audio' not in request.files:
            return jsonify({'status': 'error', 'message': '沒有音頻文件'})
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'status': 'error', 'message': '沒有選擇文件'})
        
        # 保存上傳的文件
        audio_path = os.path.join(os.getcwd(), audio_file.filename)
        audio_file.save(audio_path)
        
        # 處理音頻文件
        result = process_audio_file(audio_path)
        
        # 清理上傳的文件
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    """下載文件"""
    try:
        if os.path.exists(filename):
            return send_file(filename, as_attachment=True)
        else:
            return jsonify({'status': 'error', 'message': '文件不存在'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    print("🚀 Starting Audio Transcript Fine-Tuner Server...")
    print("📱 Open your browser and go to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)