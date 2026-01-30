# 🇯🇵 AI Japanese Grammar Tutor

一個結合 AI、SRS (間隔重複系統) 與高品質語音的日語文法學習工具。

## ✨ 核心功能

- **📚 完整文法庫**：涵蓋 N5-N1 共 400+ 個文法點
- **🤖 AI 翻譯挑戰**：中翻日測驗，訓練主動產出能力
- **🔊 真人語音**：Microsoft Edge TTS (Nanami 聲音)
- **🧠 SRS 系統**：SM-2 演算法，科學化複習排程
- **📊 進度追蹤**：可視化學習數據

## 🚀 部署到 Streamlit Cloud

1. **前往 [Streamlit Cloud](https://streamlit.io/cloud)**
2. 使用 GitHub 帳號登入
3. 點擊 **"New app"**
4. 選擇：
   - **Repository**: `lawmingyun123/Japanese-Gramma-Learning-`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. 在 **Advanced settings** 中設定環境變數：
   - **GEMINI_API_KEY**: 您的 Google Gemini API Key
6. 點擊 **"Deploy"**

## 🛠️ 本地運行

```bash
# 安裝依賴
pip install -r requirements.txt

# 設定 API Key (.env 檔案)
echo "GEMINI_API_KEY=your_api_key_here" > .env

# 啟動應用
streamlit run app.py
```

## 📖 使用方式

1. 在側邊欄輸入 Gemini API Key
2. 點擊 **「開始複習」**
3. 系統會依難度 (N5→N1) 準備題目
4. 翻譯中文句子成日文
5. AI 分析並提供標準發音
6. 根據熟悉度自我評分

## 🧩 技術棧

- **Frontend**: Streamlit
- **AI**: Google Gemini 2.5 Flash
- **TTS**: Edge-TTS
- **Database**: SQLite
- **SRS**: SuperMemo-2

## 📝 License

MIT

---

Made with ❤️ for Japanese learners
