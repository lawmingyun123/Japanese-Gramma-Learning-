# Implementation Plan - Quiz & UI Refinement

## Goal Description
Address user feedback to make the quiz more challenging and meaningful, ensure audio works, and structure learning by difficulty.

## Proposed Changes

### 1. Translation Quiz Mode
#### [MODIFY] [ai_tutor.py](file:///c:/Users/user/Desktop/MyFile/Self-Software/Agent%20Skill%20Antigravity/Japanese-Learning-Agent/ai_tutor.py)
- **Prompt Update**: Change `generate_lesson_content` prompt.
    - Instead of "Fill in the blank" or "Example Sentence", ask for:
    - `question`: A Chinese sentence (e.g., "在等電車這段期間，看了一本書。").
    - `context`: The grammar context.
    - User goal: Translate this Chinese sentence into Japanese using the target grammar.

### 2. Audio Player Fix
#### [MODIFY] [app.py](file:///c:/Users/user/Desktop/MyFile/Self-Software/Agent%20Skill%20Antigravity/Japanese-Learning-Agent/app.py)
- **Path Issue**: Streamlit might not serve files from absolute paths outside its static folder easily.
- **Fix**: 
    - Verify `st.audio` can read the absolute path.
    - OR read bytes in python and pass bytes to `st.audio`.
    
### 3. Level-Based Sorting
#### [MODIFY] [database_manager.py](file:///c:/Users/user/Desktop/MyFile/Self-Software/Agent%20Skill%20Antigravity/Japanese-Learning-Agent/database_manager.py)
- **Query Update**: In `get_due_reviews`, add `ORDER BY grammar_points.jlpt_level DESC` (N5 is usually "N5", N1 is "N1").
    - Wait, string sort: N1 < N2 ... N5.
    - User wants Easy -> Hard (N5 -> N1).
    - So Sort Descending? "N5" > "N4" ... "N1". 
    - Let's check the values. If stored as "N5", "N1". 
    - "N5" > "N1". So DESC sort gives N5 first? 
    - Actually, let's implement a custom sort in Python or map levels to integers (5,4,3,2,1) in SQL case statement if possible, or just sort in Python after fetch.

## Verification Plan
1. **Quiz**: Start session, verify question is Chinese text.
2. **Audio**: Verify player appears and sound plays.
3. **Sort**: Check the order of the first few cards (should be N5 first).
