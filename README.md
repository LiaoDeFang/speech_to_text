# 🎙️ Audio Transcript Fine-Tuner

## 📋 完整文件清單

您需要創建以下文件：

1. **`transcribe_large_audio.py`** - 主要的轉錄腳本
2. **`app.py`** - Flask 服務器
3. **`requirements.txt`** - 依賴包清單
4. **`README.md`** - 本說明文件

## 🚀 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 啟動服務器
```bash
python app.py
```

### 3. 打開瀏覽器
訪問：http://localhost:5000

## 📁 文件結構
```
your-project/
├── transcribe_large_audio.py  # 主要轉錄腳本
├── app.py                     # Flask 服務器
├── requirements.txt           # 依賴包
└── README.md                 # 說明文件
```

## ✨ 功能特色

- **拖放上傳**: 直接拖放音頻文件
- **自動分割**: 大文件自動分割處理
- **雙重輸出**: 
  - 原始 Whisper 轉錄
  - GPT-4.1 改善版本
- **在線預覽**: 點擊查看文件內容
- **一鍵下載**: 下載 Markdown 格式文件

## 🔧 配置說明

在 `transcribe_large_audio.py` 中，您的配置已經設置好：

```python
API_KEY = "您的API密鑰"
AZURE_ENDPOINT = "https://silve-magk0is1-eastus2.cognitiveservices.azure.com/"
WHISPER_MODEL = "my-gemini-recorder"
GPT_MODEL = "my-gemini-finetuner"
```

## 🎯 使用步驟

1. **啟動服務器**: 運行 `python app.py`
2. **打開瀏覽器**: 訪問 http://localhost:5000
3. **上傳音頻**: 拖放或選擇音頻文件
4. **開始處理**: 點擊「開始轉錄並生成改善版本」
5. **查看結果**: 點擊「查看」按鈕預覽內容
6. **下載文件