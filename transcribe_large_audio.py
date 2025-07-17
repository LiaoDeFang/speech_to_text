import os
import json
import sys
from pydub import AudioSegment
import math

# 嘗試導入 OpenAI，如果失敗則給出清晰的錯誤信息
try:
    from openai import AzureOpenAI
except ImportError as e:
    print("❌ OpenAI 庫導入失敗！")
    print("請運行: pip install --upgrade openai")
    sys.exit(1)

# --- Configuration ---
API_KEY = "5xF9YpUcEKxYt6IhIBywab0gAuQEMoJhtpASxkVuSPSQjSFGcgMmJQQJ99BEACHYHv6XJ3w3AAAAACOGYygR"
AZURE_ENDPOINT = "https://silve-magk0is1-eastus2.cognitiveservices.azure.com/"
WHISPER_MODEL = "my-gemini-recorder"
GPT_MODEL = "my-gemini-finetuner"
WHISPER_API_VERSION = "2024-06-01"
GPT_API_VERSION = "2024-12-01-preview"

def test_openai_version():
    """測試 OpenAI 庫版本"""
    try:
        import openai
        print(f"✅ OpenAI 版本: {openai.__version__}")
        
        # 測試 AzureOpenAI 初始化
        client = AzureOpenAI(
            api_key="test",
            api_version="2024-06-01",
            azure_endpoint="https://test.openai.azure.com/"
        )
        print("✅ AzureOpenAI 客戶端初始化成功")
        return True
    except Exception as e:
        print(f"❌ OpenAI 庫測試失敗: {e}")
        return False

def split_audio(file_path, max_size_mb=25):
    """Splits an audio file into chunks under a specific size."""
    audio = AudioSegment.from_file(file_path)
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    if file_size_mb <= max_size_mb:
        return [file_path]

    num_chunks = math.ceil(file_size_mb / max_size_mb)
    duration_ms = len(audio)
    chunk_duration_ms = math.ceil(duration_ms / num_chunks)
    
    chunks = []
    temp_dir = "temp_audio_chunks"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    for i in range(num_chunks):
        start_ms = i * chunk_duration_ms
        end_ms = min((i + 1) * chunk_duration_ms, duration_ms)
        chunk = audio[start_ms:end_ms]
        chunk_path = os.path.join(temp_dir, f"chunk_{i+1}.mp3")
        chunk.export(chunk_path, format="mp3")
        chunks.append(chunk_path)

    return chunks

def transcribe_chunk(client, chunk_path):
    """Transcribes a single audio chunk using the Whisper API."""
    try:
        with open(chunk_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model=WHISPER_MODEL,
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        return f"[轉錄錯誤: {e}]"

def fine_tune_transcript(client, raw_transcript, filename):
    """Uses GPT-4.1 to improve and format the transcript."""
    prompt = f"""請改善此音頻轉錄，重點包括：

1. **Grammar and Punctuation**: Fix grammar errors, add proper punctuation, and correct sentence structure
2. **Formatting**: Organize into clear paragraphs and proper markdown format
3. **Speaker Identification**: If multiple speakers are detected, separate them clearly
4. **Filler Words**: Remove excessive "um", "uh", "like", "you know", etc.
5. **Clarity**: Make the text more readable while preserving the original meaning
6. **Structure**: Add appropriate headings if the content has clear sections/topics

**Original Transcript:**
{raw_transcript}

**Instructions:**
- Maintain the original meaning and context
- Use proper markdown formatting
- If there are multiple speakers, use "**Speaker 1:**", "**Speaker 2:**" format
- Add a brief title at the top based on the content
- Keep the improved text natural and conversational

Please provide the improved transcript in markdown format:"""

    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert transcript editor. Improve transcripts while preserving original meaning and context."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"# Fine-tuning Error\n\nCould not process with GPT-4.1: {e}\n\n## Original Transcript\n{raw_transcript}"

def create_azure_client(api_version):
    """創建 Azure OpenAI 客戶端"""
    try:
        return AzureOpenAI(
            api_key=API_KEY,
            api_version=api_version,
            azure_endpoint=AZURE_ENDPOINT
        )
    except Exception as e:
        print(f"❌ 無法創建 Azure OpenAI 客戶端: {e}")
        return None

def process_audio_file(audio_file_path):
    """Main processing function that returns results as JSON."""
    try:
        print("🔍 測試 OpenAI 庫...")
        if not test_openai_version():
            return {'status': 'error', 'message': 'OpenAI 庫版本不相容'}

        print("🎙️ 初始化 Whisper 客戶端...")
        whisper_client = create_azure_client(WHISPER_API_VERSION)
        if not whisper_client:
            return {'status': 'error', 'message': '無法創建 Whisper 客戶端'}

        print("📄 處理音頻文件...")
        chunks = split_audio(audio_file_path)
        full_transcript = []

        for i, chunk_path in enumerate(chunks, 1):
            print(f"🔄 轉錄分段 {i}/{len(chunks)}")
            text = transcribe_chunk(whisper_client, chunk_path)
            full_transcript.append(text)

        # Combine Raw Transcript
        raw_transcript = "\n".join(full_transcript)
        base_filename = os.path.splitext(os.path.basename(audio_file_path))[0]
        
        # Save No-Modified Version
        no_modified_filename = f"{base_filename}_No-modified.md"
        with open(no_modified_filename, 'w', encoding='utf-8') as f:
            f.write(f"# Raw Transcript - {base_filename}\n\n")
            f.write(f"*Original audio file: {os.path.basename(audio_file_path)}*\n\n")
            f.write("---\n\n")
            f.write(raw_transcript)
        
        print("✨ 初始化 GPT-4.1 客戶端...")
        gpt_client = create_azure_client(GPT_API_VERSION)
        if not gpt_client:
            return {'status': 'error', 'message': '無法創建 GPT-4.1 客戶端'}
        
        print("🔧 使用 GPT-4.1 改善內容...")
        fine_tuned_transcript = fine_tune_transcript(gpt_client, raw_transcript, base_filename)
        
        # Save Fine-tuned Version
        fine_tuned_filename = f"{base_filename}_Fine-tuned.md"
        with open(fine_tuned_filename, 'w', encoding='utf-8') as f:
            f.write(fine_tuned_transcript)

        # Cleanup
        if os.path.exists("temp_audio_chunks"):
            for chunk_file in os.listdir("temp_audio_chunks"):
                os.remove(os.path.join("temp_audio_chunks", chunk_file))
            os.rmdir("temp_audio_chunks")

        print("✅ 處理完成！")
        return {
            'status': 'success',
            'files': [
                {
                    'name': no_modified_filename,
                    'type': 'No-modified',
                    'content': f"# Raw Transcript - {base_filename}\n\n*Original audio file: {os.path.basename(audio_file_path)}*\n\n---\n\n{raw_transcript}"
                },
                {
                    'name': fine_tuned_filename,
                    'type': 'Fine-tuned',
                    'content': fine_tuned_transcript
                }
            ]
        }

    except Exception as e:
        print(f"❌ 處理錯誤: {e}")
        return {'status': 'error', 'message': str(e)}

def main():
    print("🎙️ Audio Transcript Fine-Tuner")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        # Command line mode
        audio_file_path = sys.argv[1]
        result = process_audio_file(audio_file_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Interactive mode
        audio_file_path = input("Please drag and drop your audio file here and press Enter: ").strip().replace('"', '')
        
        if not os.path.exists(audio_file_path):
            print("Error: File not found. Please make sure the path is correct.")
            return
            
        result = process_audio_file(audio_file_path)
        
        if result['status'] == 'success':
            print(f"\n=== Transcription Complete! ===")
            for file_info in result['files']:
                print(f"✓ {file_info['name']}")
        else:
            print(f"Error: {result['message']}")

if __name__ == "__main__":
    main()