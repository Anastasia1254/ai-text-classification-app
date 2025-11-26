from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import sqlite3
from io import BytesIO
from xhtml2pdf import pisa
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os

from model import summarize  # твоя модель


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/wordclouds'


def save_article(title, text, summary):
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            text TEXT,
            summary TEXT
        )
    """)

    c.execute(
        "INSERT INTO articles (title, text, summary) VALUES (?, ?, ?)",
        (title, text, summary)
    )

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


def generate_wordcloud(text, save_path):
    font_path = os.path.abspath(os.path.join('fonts', 'DejaVuSans.ttf'))

    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Шрифт не знайдено: {font_path}")

    try:
        wc = WordCloud(
            width=800,
            height=400,
            background_color='white',
            font_path=font_path
        ).generate(text)
    except Exception as e:
        print(f"Помилка генерації WordCloud: {e}")
        return None

    plt.figure(figsize=(10, 5))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(save_path)
    plt.close()

    return save_path


def get_ai_results():
    """Повертає список з текстом, summary та фейковим sentiment."""
    articles = get_articles()
    results = []

    for art in articles:
        ai_summary = summarize(art[2])

        # фейковий sentiment
        sentiment = "positive" if len(art[2]) % 2 == 0 else "negative"

        results.append({
            "id": art[0],
            "title": art[1],
            "text": art[2],
            "summary": ai_summary,
            "sentiment": sentiment
        })

    return results


@app.route('/')
def index():
    articles = get_articles()
    return render_template('index.html', articles=articles)


@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        text = request.form['text']
        summary = summarize(text)  # модель сумаризації

        save_article(title, text, summary)
        return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/article/<int:id>')
def article(id):
    art = get_article(id)
    if not art:
        return "Стаття не знайдена", 404

    # Генерація WordCloud
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    wc_path = os.path.join(app.config['UPLOAD_FOLDER'], f'wc_{id}.png')

    generate_wordcloud(art[3], wc_path)

    return render_template('article.html', article=art, wordcloud_path=wc_path)


@app.route('/download/<int:id>')
def download(id):
    art = get_article(id)

    if not art:
        return "Стаття не знайдена", 404

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

    return send_file(pdf, download_name=f"{art[1]}.pdf", as_attachment=True)



@app.route('/reports')
def reports():
    results = get_ai_results()

    # Підсумки по sentiment
    summary = {}
    for r in results:
        summary[r['sentiment']] = summary.get(r['sentiment'], 0) + 1

    return render_template('reports.html', reports=results, summary=summary)


@app.route('/reports.json')
def reports_json():
    articles = [
        {
            "title": art[1],
            "summary": art[3],
            "text": art[2],
            "sentiment": {"Positive": 2, "Neutral": 1, "Negative": 0}  # приклад
        }
        for art in get_articles()
    ]

    return jsonify(articles)


if __name__ == '__main__':
    app.run(debug=True)
