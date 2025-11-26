from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
from io import BytesIO
from xhtml2pdf import pisa
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os
from model import summarize  # тепер використовуємо твою модель

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/wordclouds'

# -----------------------
# Функції для роботи з базою даних
# -----------------------
def save_article(title, text, summary):
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    c.execute("INSERT INTO articles (title, text, summary) VALUES (?, ?, ?)", (title, text, summary))
    conn.commit()
    conn.close()

def get_articles():
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    c.execute("SELECT * FROM articles ORDER BY id DESC")
    articles = c.fetchall()
    conn.close()
    return articles

def get_article(id):
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    c.execute("SELECT * FROM articles WHERE id=?", (id,))
    art = c.fetchone()
    conn.close()
    return art

# -----------------------
# Routes
# -----------------------
@app.route('/')
def index():
    articles = get_articles()
    return render_template('index.html', articles=articles)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        text = request.form['text']
        summary = summarize(text)  # виклик твоєї моделі
        save_article(title, text, summary)
        return redirect(url_for('index'))
    return render_template('create.html')

@app.route('/article/<int:id>')
def article(id):
    art = get_article(id)
    
    # Генерація WordCloud для summary
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(art[3])
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    wc_path = os.path.join(app.config['UPLOAD_FOLDER'], f'wc_{id}.png')
    plt.figure(figsize=(10,5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(wc_path)
    plt.close()
    
    return render_template('article.html', article=art, wordcloud_path=wc_path)

@app.route('/download/<int:id>')
def download(id):
    art = get_article(id)
    html = f"""
    <h1>{art[1]}</h1>
    <h3>Summary:</h3>
    <p>{art[3]}</p>
    <h3>Full Text:</h3>
    <p>{art[2]}</p>
    """
    pdf = BytesIO()
    pisa.CreatePDF(html, dest=pdf)
    pdf.seek(0)
    return send_file(pdf, attachment_filename=f"{art[1]}.pdf", as_attachment=True)

# -----------------------
# Запуск серверу
# -----------------------
if __name__ == '__main__':
    app.run(debug=True)
