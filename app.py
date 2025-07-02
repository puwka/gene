import os
from flask import Flask, render_template, request, send_file, jsonify
from dotenv import load_dotenv
import openai

load_dotenv()

app = Flask(__name__)
openai_api_key = os.getenv('OPENAI_API_KEY')
client = openai.Client(api_key=openai_api_key)

GENERATED_FILE = 'generated_site.html'

PROMPT_TEMPLATE = (
    "Создай адаптивный одностраничный сайт в стиле '{style}' по описанию: {desc}. "
    "Весь CSS помести внутрь <style>. Не добавляй пояснений, только валидный HTML-код."
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    desc = data.get('description', '')
    style = data.get('style', 'минимализм')
    prompt = PROMPT_TEMPLATE.format(style=style, desc=desc)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.7
        )
        html_code = response.choices[0].message.content
        with open(GENERATED_FILE, 'w', encoding='utf-8') as f:
            f.write(html_code)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/preview')
def preview():
    if not os.path.exists(GENERATED_FILE):
        return 'Файл не найден', 404
    with open(GENERATED_FILE, 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/download')
def download():
    if not os.path.exists(GENERATED_FILE):
        return 'Файл не найден', 404
    return send_file(GENERATED_FILE, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True) 