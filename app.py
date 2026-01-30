import streamlit as st
import pandas as pd
import json
import os
import time
import uuid
import shutil
from datetime import datetime
import audio_manager
from database_manager import DatabaseManager
from srs_engine import SRSEngine
from ai_tutor import AITutor
from dotenv import load_dotenv

load_dotenv()

# Cleanup temp audio on start (Only once per session)
if 'cleanup_done' not in st.session_state:
    if os.path.exists(audio_manager.OUTPUT_DIR):
        try:
            shutil.rmtree(audio_manager.OUTPUT_DIR)
        except Exception:
            pass # Ignore if file in use
    os.makedirs(audio_manager.OUTPUT_DIR, exist_ok=True)
    st.session_state.cleanup_done = True
    
# Ensure dir exists even if not first run (e.g. manual delete)
if not os.path.exists(audio_manager.OUTPUT_DIR):
    os.makedirs(audio_manager.OUTPUT_DIR, exist_ok=True)

# Page Configuration
st.set_page_config(
    page_title="AI Japanese Tutor",
    page_icon="🇯🇵",
    layout="wide"
)

# --- AUTHENTICATION ---
def check_password():
    """Returns True if the user has entered the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state.get("password") == st.secrets.get("AUTH_PASSWORD", ""):
            st.session_state["password_correct"] = True
            if "password" in st.session_state:
                del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.title("🔐 AI 日語導師 - 登入")
        st.text_input(
            "請輸入密碼", type="password", on_change=password_entered, key="password"
        )
        st.info("ℹ️ 此系統需要密碼保護以防止 API 濫用")
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error
        st.title("🔐 AI 日語導師 - 登入")
        st.text_input(
            "請輸入密碼", type="password", on_change=password_entered, key="password"
        )
        st.error("❌ 密碼錯誤，請重試")
        return False
    else:
        # Password correct
        return True

if not check_password():
    st.stop()  # Do not continue if password is not correct


# --- SIDEBAR & SETUP ---
with st.sidebar:
    st.title("🇯🇵 AI 日語導師")
    
    # API Key Input
    api_key = st.text_input("🔑 Gemini API Key", type="password", help="請輸入 Google Gemini API Key 以啟用 AI 功能")
    
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
    
    menu = st.radio("功能選單", ["📚 學習與複習", "📊 學習數據", "🗂️ 文法庫"])
    
    st.divider()
    
    # Backup Section
    st.write("### 💾 資料備份")
    
    # Export Progress
    if st.button("📤 匯出學習進度"):
        export_data = st.session_state.db.export_progress()
        export_json = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        st.download_button(
            label="⬇️ 下載 JSON 檔案",
            data=export_json,
            file_name=f"japanese_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        st.success(f"✅ 已準備 {export_data['total_items']} 筆記錄")
    
    # Import Progress
    uploaded_file = st.file_uploader("📥 匯入學習進度", type=['json'])
    if uploaded_file is not None:
        try:
            import_data = json.load(uploaded_file)
            result = st.session_state.db.import_progress(import_data)
            
            st.success(f"""
            ✅ 匯入完成！
            - 新增：{result['added']} 筆
            - 更新：{result['updated']} 筆
            - 跳過：{result['skipped']} 筆
            """)
            st.rerun()
        except Exception as e:
            st.error(f"❌ 匯入失敗：{e}")
    
    st.divider()
    
    # Stats Preview
    if 'db' in st.session_state:
        stats = st.session_state.db.get_stats()
        st.write("### 學習狀態")
        col1, col2 = st.columns(2)
        col1.metric("新卡片", stats.get('new', 0))
        col2.metric("複習中", stats.get('active', 0))

# Initialize Components
if 'db' not in st.session_state:
    st.session_state.db = DatabaseManager()
    
    # Check for seed data
    # Check for seed data and import
    try:
        # Define seed files to look for
        seed_files = [
            'seed_data.json', 
            'grammar_n4.json', 
            'grammar_n3.json', 
            'grammar_n2.json', 
            'grammar_n1.json'
        ]
        
        imported_count = 0
        for filename in seed_files:
            seed_path = os.path.join(os.path.dirname(__file__), filename)
            if os.path.exists(seed_path):
                with open(seed_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        st.session_state.db.add_grammar_point(
                            item['level'], item['concept'], item['meaning'], 
                            item['structure'], item['explanation'], item.get('tags', '')
                        )
                    imported_count += 1
        
        if imported_count > 0:
             # Only show toast if actually imported something new? 
             # DatabaseManager.add_grammar_point handles duplicates now, so safe to run.
             pass 

    except Exception as e:
        st.error(f"資料庫匯入錯誤: {e}")

# Initialize AI with key from input or env
current_api_key = api_key or os.getenv("GEMINI_API_KEY")
st.session_state.ai = AITutor(api_key=current_api_key)

# Session State for Review Flow
if 'review_queue' not in st.session_state:
    st.session_state.review_queue = [] # List of prepared cards
if 'current_card' not in st.session_state:
    st.session_state.current_card = None
if 'review_step' not in st.session_state:
    st.session_state.review_step = 'question' # question, feedback
if 'last_feedback' not in st.session_state:
    st.session_state.last_feedback = None
if 'last_user_input' not in st.session_state:
    st.session_state.last_user_input = ""

# --- FUNCTIONS ---
def prepare_session():
    """Fetches due items and pre-generates AI content for all of them."""
    
    # 1. Fetch Candidates
    # We fetch up to 10 items for a batch session
    reviews_data = st.session_state.db.get_due_reviews()
    candidates = reviews_data['reviews'] + reviews_data['new']
    candidates = candidates[:10] # Limit batch size
    
    if not candidates:
        st.toast("目前沒有需要複習的內容！", icon="🎉")
        return

    # 2. Batch Generation Loop
    progress_text = "AI 正在為您準備課程中... 請稍候"
    my_bar = st.progress(0, text=progress_text)
    
    prepared_cards = []
    
    for i, card in enumerate(candidates):
        # Update progress bar
        percent = int(((i) / len(candidates)) * 100)
        my_bar.progress(percent, text=f"正在生成第 {i+1}/{len(candidates)} 題: {card['grammar_concept']}...")
        
        # Generate AI Content
        try:
            ai_content = st.session_state.ai.generate_lesson_content(card)
            
            # Generate Audio for the Answer (Japanese)
            audio_filename = f"{uuid.uuid4()}.mp3"
            target_sentence = ai_content.get('example_sentence', ai_content.get('question', ''))
            # Ensure we are generating for Japanese text
            audio_path = audio_manager.generate_audio(target_sentence, audio_filename)
            ai_content['audio_path'] = audio_path
            
            card.update(ai_content)
            prepared_cards.append(card)
        except Exception as e:
            print(f"Error generating card {card['grammar_concept']}: {e}")
            # Skip failed cards or add fallback? 
            # Current logic in ai_tutor returns a fallback dictionary on error, so it's safe.
            card.update({"question": "AI 生成失敗", "hint": "", "context": "Error"})
            prepared_cards.append(card)
            
    my_bar.progress(100, text="準備完成！")
    time.sleep(0.5)
    my_bar.empty()
    
    # 3. Update State
    st.session_state.review_queue = prepared_cards
    load_next_from_queue()

def load_next_from_queue():
    """Pops the next card from the review queue."""
    if st.session_state.review_queue:
        st.session_state.current_card = st.session_state.review_queue.pop(0)
        st.session_state.review_step = 'question'
        st.session_state.last_feedback = None
        st.session_state.last_user_input = ""
    else:
        st.session_state.current_card = None

def process_rating(quality):
    card = st.session_state.current_card
    
    # Calculate SRS update
    result = SRSEngine.calculate_review(
        quality, 
        card['repetition'], 
        card['efactor'], 
        card['interval']
    )
    
    # Update DB
    st.session_state.db.update_progress(
        card['progress_id'],
        card['grammar_id'],
        quality,
        result['interval'],
        result['efactor'],
        result['repetition'],
        result['next_review_date']
    )
    
    # Load next
    if st.session_state.review_queue:
        st.toast(f"已記錄！剩餘 {len(st.session_state.review_queue)} 題", icon="✅")
        load_next_from_queue()
        st.rerun()
    else:
        st.balloons()
        st.session_state.current_card = None # End state
        st.rerun()

# --- MAIN PAGE ---

if menu == "📚 學習與複習":
    st.header("練習室")
    
    if not current_api_key:
        st.warning("請先在左側輸入 Gemini API Key 以啟用 AI 功能。")
    
    # Logic:
    # 1. If we have a current card => Show Card
    # 2. If no current card AND queue has items => Load next (Shouldn't happen logic wise usually unless refresh)
    # 3. If no current card AND queue empty => Show "Start Session" Button
    
    if st.session_state.current_card:
        # --- REVIEW INTERFACE ---
        card = st.session_state.current_card
        
        # Progress (Queue based)
        # Note: We don't know total initial size here unless we stored it, but simple remaining count is fine
        st.caption(f"本輪剩餘題目: {len(st.session_state.review_queue) + 1}")
        
        with st.container(border=True):
            st.subheader(f"{card['grammar_concept']}")
            st.caption(f"級數: {card.get('level', 'N5')} | 核心語意: {card['meaning']}")
            st.info(f"💡 文法結構: {card['structure']}")
            
            st.markdown(f"### 題目\n{card['question']}")
            
            if card.get('hint'):
                with st.expander("查看提示"):
                    st.text(card['hint'])
            
            # Interaction Area
            if st.session_state.review_step == 'question':
                user_input = st.text_area("請輸入您的回答 (日文):", key="user_input_box", height=100)
                
                # Check for Ctrl+Enter or Command+Enter shortcut could be added via JS, but st.button is standard
                if st.button("提交答案", type="primary"):
                    if user_input.strip():
                        st.session_state.last_user_input = user_input # Save input
                        with st.spinner("AI 正在分析您的句子..."):
                            feedback = st.session_state.ai.evaluate_response(user_input, card)
                        st.session_state.last_feedback = feedback
                        st.session_state.review_step = 'feedback'
                        st.rerun()
                    else:
                        st.warning("請輸入內容！")
                        
            elif st.session_state.review_step == 'feedback':
                st.markdown("---")
                # Show User's Answer
                st.markdown("### 您的回答")
                st.info(st.session_state.last_user_input)

                st.markdown("### AI 分析回饋")
                feedback = st.session_state.last_feedback
                
                score = feedback.get('score', 0)
                if score >= 4:
                    st.success(f"評價: {feedback.get('feedback', '')}")
                elif score >= 2:
                    st.warning(f"評價: {feedback.get('feedback', '')}")
                else:
                    st.error(f"評價: {feedback.get('feedback', '')}")
                
                if feedback.get('correction'):
                    st.markdown("**✍️ 修正建議:**")
                    st.code(feedback['correction'], language='text')

                 # Audio Player (Correct Answer)
                if card.get('audio_path'):
                     if os.path.exists(card['audio_path']):
                         st.markdown("### 🔊 發音示範")
                         with open(card['audio_path'], 'rb') as audio_file:
                            audio_bytes = audio_file.read()
                         st.audio(audio_bytes, format="audio/mp3")
                     else:
                         st.error(f"⚠️ 找不到語音檔: {card['audio_path']}")
                else:
                    st.warning("⚠️ 此題目未生成語音")
                
                # Correct Answer Display (The original target)
                if card.get('example_sentence'):
                    st.markdown("**✅ 問題的正確答案:**")
                    st.success(card['example_sentence'])
                
                # feedback['better_sentence'] removed as per user request

                st.write("### 自我評分 (影響下次複習時間)")
                cols = st.columns(6)
                with cols[0]:
                    if st.button("0 - 完全忘記"): process_rating(0)
                with cols[1]:
                    if st.button("1 - 錯誤"): process_rating(1)
                with cols[2]:
                    if st.button("2 - 困難"): process_rating(2)
                with cols[3]:
                    if st.button("3 - 普通"): process_rating(3)
                with cols[4]:
                    if st.button("4 - 良好"): process_rating(4)
                with cols[5]:
                    if st.button("5 - 完美"): process_rating(5)

    else:
        # --- START SCREEN ---
        st.subheader("準備好開始學習了嗎？")
        
        # Check pending reviews
        reviews_data = st.session_state.db.get_due_reviews()
        total_due = len(reviews_data['reviews']) + len(reviews_data['new'])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("今日待複習", len(reviews_data['reviews']))
        col2.metric("今日新卡片", len(reviews_data['new']))
        
        st.write("---")
        
        if total_due > 0:
            st.write(f"共有 **{total_due}** 個項目待處理。")
            st.write("點擊下方按鈕開始。系統將會花一點時間預先生成題目，讓您的學習過程更流暢。")
            
            if st.button("🚀 開始學習 (批次生成)", type="primary"):
                prepare_session()
                st.rerun()
        else:
            st.success("🎉 太棒了！今天沒有需要複習的內容。")
            if st.button("複習隨機內容 (額外練習)"):
                # Potential feature: Review random learned cards
                st.info("功能開發中...")

elif menu == "📊 學習數據":
    st.header("學習統計")
    # stats = st.session_state.db.get_stats() # Already fetched
    st.json(stats)
    
    st.subheader("即將到來的複習")
    due = st.session_state.db.get_due_reviews()
    if due['reviews']:
        st.table(pd.DataFrame(due['reviews'])[['grammar_concept', 'interval', 'repetition']])
    else:
        st.info("目前沒有積壓的複習。")

elif menu == "🗂️ 文法庫":
    st.header("文法知識庫")
    conn = st.session_state.db.get_connection()
    df = pd.read_sql("SELECT * FROM grammar_points", conn)
    st.dataframe(df)
    conn.close()
