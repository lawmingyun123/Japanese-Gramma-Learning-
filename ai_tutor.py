import google.generativeai as genai
import json
import os

class AITutor:
    def __init__(self, api_key=None):
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
            try:
                # Dynamic Model Selection
                valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                # Priority list (Try all Flash variants first)
                priorities = [
                    'gemini-2.5-flash',
                    'gemini-2.0-flash',
                    'models/gemini-2.5-flash', # Some APIs use models/ prefix
                    'models/gemini-2.0-flash',
                    'gemini-1.5-flash', 
                    'gemini-1.5-flash-001', 
                    'gemini-1.5-flash-latest', 
                    'gemini-1.5-flash-8b',
                    'gemini-1.5-pro',
                    'gemini-1.5-pro-001'
                ]
                selected_model = None
                
                for p in priorities:
                    # Check for exact or close match (some apis return models/gemini-1.5-flash-001)
                    matches = [vm for vm in valid_models if p in vm]
                    if matches:
                        selected_model = matches[0] # Pick the first match (usually latest)
                        break
                
                if not selected_model and valid_models:
                    selected_model = valid_models[0] # Fallback to anything available
                
                if selected_model:
                    self.model = genai.GenerativeModel(selected_model)
                    print(f"Selected Model: {selected_model}")
                else:
                    self.model = None
                    print("No valid generation models found.")
                    
            except Exception as e:
                print(f"Model selection error: {e}")
                self.model = genai.GenerativeModel('gemini-pro') # Hard fallback 
        else:
            self.model = None

    def generate_lesson_content(self, grammar_point):
        """
        Generates a challenge for the user.
        """
        concept = grammar_point['grammar_concept']
        meaning = grammar_point.get('meaning', '')
        
        if not self.model:
            # Fallback for no API key
            return {
                "question": f"請使用「{concept}」造一個與日常與生活相關的句子。\n(請在左側 Sidebar 輸入 API Key 以啟用 AI 題目生成)",
                "hint": f"這個文法的意思是：{meaning}",
                "context": "系統預設模式"
            }

        try:
            prompt = f"""
            Task: Create a translation challenge for Japanese grammar: {concept}.
            
            Requirements:
            1. Create a natural Japanese sentence using {concept}.
            2. Output the Traditional Chinese translation of this sentence as the "question". (e.g. "請翻譯：...")
            3. The user's goal is to translate this Chinese sentence back into Japanese.
            4. Provide the grammar context.
            5. Provide a hint (e.g. key vocabulary).
            
            Output format (JSON):
            {{
                "question": "The Chinese sentence to be translated",
                "context": "Explanation of grammar nuances",
                "hint": "Optional vocabulary hint",
                "example_sentence": "The correct Japanese sentence"
            }}
            """
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
            return {
                "question": f"請造句 using: {concept} (AI 生成失敗: {str(e)})",
                "hint": "",
                "context": "Error Fallback"
            }

    def evaluate_response(self, user_input, grammar_point):
        """
        Evaluates the user's sentence.
        """
        concept = grammar_point['grammar_concept']
        
        if not self.model:
            return {
                "feedback": "請輸入 API Key 來啟用 AI 批改功能。",
                "correction": "無法連線至 AI。",
                "score": 0,
                "better_sentence": ""
            }

        try:
            prompt = f"""
            Role: Japanese Grammar Expert.
            Task: Evaluate student sentence.
            Target Grammar: {concept}
            Student Input: {user_input}
            
            Strict Rules:
            1. Output ONLY JSON. No markdown formatting.
            2. NO praise, encouragement, or filler text.
            3. Analysis must be extremely concise (logic only, under 30 chars).
            4. Traditional Chinese (繁體中文).
            
            Output format (JSON):
            {{
                "feedback": "Analysis of logic/grammar only",
                "correction": "Corrected sentence (if needed, else null)",
                "better_sentence": "One natural native example",
                "score": 3
            }}
            """
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
             return {
                "feedback": f"AI 分析發生錯誤: {str(e)}",
                "correction": None,
                "better_sentence": None,
                "score": 0
            }
