"""
測試音檔智能管理功能

此腳本驗證：
1. 音檔可以正常生成
2. 相同文本會重複使用同一個音檔
3. 音檔路徑正確且檔案存在
"""

import sys
import os

# 添加專案路徑
sys.path.insert(0, os.path.dirname(__file__))

from audio_manager import generate_audio
import hashlib

def test_audio_generation():
    print("=" * 60)
    print("測試音檔智能管理功能")
    print("=" * 60)
    
    # 測試文本
    test_sentences = [
        "こんにちは、元気ですか。",
        "今日はいい天気ですね。",
        "こんにちは、元気ですか。"  # 重複的句子
    ]
    
    print("\n1️⃣ 測試音檔生成")
    print("-" * 60)
    
    for i, sentence in enumerate(test_sentences, 1):
        # 計算預期的檔名
        audio_key = hashlib.md5(sentence.encode('utf-8')).hexdigest()
        expected_filename = f"{audio_key}.mp3"
        
        print(f"\n測試 {i}: {sentence}")
        print(f"預期檔名: {expected_filename}")
        
        # 生成音檔
        audio_path = generate_audio(sentence, expected_filename)
        
        if audio_path and os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            print(f"✅ 成功: {audio_path}")
            print(f"   檔案大小: {file_size} bytes")
        else:
            print(f"❌ 失敗: 音檔未生成或不存在")
    
    print("\n" + "=" * 60)
    print("2️⃣ 測試重複使用檢查")
    print("-" * 60)
    
    # 再次生成第一個句子
    sentence1 = test_sentences[0]
    audio_key1 = hashlib.md5(sentence1.encode('utf-8')).hexdigest()
    filename1 = f"{audio_key1}.mp3"
    
    print(f"\n再次生成: {sentence1}")
    print("預期行為: 應該直接重複使用，不重新生成")
    
    audio_path = generate_audio(sentence1, filename1)
    
    if audio_path:
        print(f"✅ 路徑返回: {audio_path}")
        print("   (檢查終端輸出，應顯示 'File already exists, reusing')")
    else:
        print("❌ 失敗")
    
    print("\n" + "=" * 60)
    print("3️⃣ 檢查 temp_audio 資料夾")
    print("-" * 60)
    
    temp_audio_dir = os.path.join(os.path.dirname(__file__), "temp_audio")
    if os.path.exists(temp_audio_dir):
        files = [f for f in os.listdir(temp_audio_dir) if f.endswith('.mp3')]
        print(f"\n音檔總數: {len(files)}")
        print(f"預期數量: 2 (因為第 1 和第 3 個句子相同)")
        
        for file in files[:5]:  # 只顯示前 5 個
            filepath = os.path.join(temp_audio_dir, file)
            size = os.path.getsize(filepath)
            print(f"  - {file} ({size} bytes)")
        
        if len(files) == 2:
            print("\n✅ 驗證通過！音檔數量正確")
        else:
            print(f"\n⚠️  音檔數量異常（預期 2，實際 {len(files)}）")
    else:
        print("❌ temp_audio 資料夾不存在")
    
    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)

if __name__ == "__main__":
    test_audio_generation()
