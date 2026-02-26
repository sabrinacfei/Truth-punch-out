from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS  
import google.generativeai as genai
import json
import re
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, resources={r"/api/search": {"origins": "*"}})

api_key = os.getenv("GEMINI_API_KEY", "").strip()  
genai.configure(api_key=api_key, transport="rest")
model = genai.GenerativeModel("gemini-2.5-flash")

@app.route('/')
def home():
    return send_from_directory('.', 'main.html')

@app.route("/health")
def health():
    return "ok", 200

@app.route("/api/search", methods=["POST"])
def search():
    data = request.get_json()
    user_input = data.get("text", "")

    prompt = f"""
    使用者說：「{user_input}」這是一句謊言。
    請根據聖經真理，回應一段經文（用中文），並寫出一段鼓勵的禱告文。
    
    請你只回傳下列格式的 JSON，不要加任何說明、標題或文字：

    {{
      "verse": "經文內容（含出處）",
      "prayer": "鼓勵的禱告文"
    }}
    """

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        print("\n📝 [Gemini 回應原始內容] ↓↓↓")
        print(response_text)

        # 嘗試擷取 JSON 區塊
        match = re.search(r'\{[\s\S]*\}', response_text)
        if not match:
            print("⚠️ 無法擷取 JSON 格式，原始文字如下：")
            return jsonify({
                "error": "無法從 Gemini 回應中擷取 JSON",
                "raw_response": response_text
            }), 500

        cleaned_json = match.group(0)

        try:
            result = json.loads(cleaned_json)
            return jsonify(result)
        except json.JSONDecodeError as json_err:
            print("❌ JSON 解析錯誤：", json_err)
            return jsonify({
                "error": "回傳內容不是有效的 JSON",
                "raw_json": cleaned_json
            }), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"伺服器錯誤：{str(e)}"
        }), 500

if __name__ == "__main__":
    app.run(debug=True, port=5002)
