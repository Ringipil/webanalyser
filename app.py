from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import validators
import networkx as nx
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import nltk
from nltk.corpus import stopwords
import base64
import json

nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

app = Flask(__name__)

def fetch_page(url):
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    response = requests.get(url)
    response.raise_for_status()
    return response.text, response.url

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        html, actual_url = fetch_page(url)
        soup = BeautifulSoup(html, 'html.parser')

        main_text = soup.get_text()
        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})

        links = [(a.text.strip(), requests.compat.urljoin(actual_url, a.get('href'))) for a in soup.find_all('a', href=True)]

        words = [word.lower() for word in main_text.split() if word.isalpha() and word.lower() not in stop_words]
        common_words = Counter(words).most_common(10)

        # Generate bar chart image for top words
        bar_chart_img = BytesIO()
        words_df = pd.DataFrame(common_words, columns=['word', 'freq'])
        plt.figure(figsize=(6, 4))
        plt.bar(words_df['word'], words_df['freq'])
        plt.title('Top 10 Words')
        plt.xlabel('Words')
        plt.ylabel('Frequency')
        plt.tight_layout()
        plt.savefig(bar_chart_img, format='png')
        plt.close()
        bar_chart_img.seek(0)
        bar_chart_data = base64.b64encode(bar_chart_img.getvalue()).decode('utf-8')

        # CSV creation
        link_statuses = []
        for text, link in links:
            if validators.url(link):
                try:
                    status = requests.get(link, timeout=5).status_code
                except:
                    status = 'Failed'
            else:
                status = 'Invalid URL'
            link_statuses.append((text, link, status))

        df_links = pd.DataFrame(link_statuses, columns=["Link text", "URL", "HTTP status"])
        csv_buffer = BytesIO()
        df_links.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        # Link graph
        G = nx.DiGraph()
        for _, link, _ in link_statuses:
            if validators.url(link):
                G.add_edge(actual_url, link)

        graph_img = BytesIO()
        plt.figure(figsize=(6,4))
        pos = nx.spring_layout(G, seed=42)
        nx.draw(G, pos, node_size=30, arrowsize=8, with_labels=False)
        nx.draw_networkx_labels(G, pos, font_size=6)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(graph_img, format='png')
        plt.close()
        graph_img.seek(0)

        return render_template('results.html',
                       url=actual_url,
                       meta_desc=meta_desc['content'] if meta_desc else 'N/A',
                       meta_keywords=meta_keywords['content'] if meta_keywords else 'N/A',
                       common_words=common_words,
                       link_statuses=link_statuses,
                       graph_img_data=base64.b64encode(graph_img.getvalue()).decode('utf-8'),
                       bar_chart_data=bar_chart_data,
                       csv_data=base64.b64encode(csv_buffer.getvalue()).decode('utf-8'))

    return render_template('index.html')

@app.route('/download_csv', methods=['POST'])
def download_csv():
    csv_base64 = request.form['csv_data']
    csv_bytes = base64.b64decode(csv_base64)
    return send_file(BytesIO(csv_bytes), download_name='links.csv', as_attachment=True)

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    from matplotlib import pyplot as plt

    url = request.form['url']
    meta_desc = request.form['meta_desc']
    meta_keywords = request.form['meta_keywords']
    words_raw = request.form['words']
    link_statuses_raw = request.form['link_statuses']

    # Parse safely
    common_words = json.loads(words_raw)
    link_statuses = json.loads(link_statuses_raw)

    # Rebuild bar chart
    bar_chart_img = BytesIO()
    word_df = pd.DataFrame(common_words, columns=["word", "freq"])
    plt.figure(figsize=(6, 3))
    plt.bar(word_df['word'], word_df['freq'])
    plt.title('Top 10 Words')
    plt.tight_layout()
    plt.savefig(bar_chart_img, format='png')
    plt.close()
    bar_chart_img.seek(0)

    # Rebuild link graph
    G = nx.DiGraph()
    for _, link, status in link_statuses:
        if validators.url(link):
            G.add_edge(url, link)

    graph_img = BytesIO()
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(6, 3))
    nx.draw(G, pos, node_size=30, arrowsize=8, with_labels=False)
    nx.draw_networkx_labels(G, pos, font_size=6)
    plt.tight_layout()
    plt.savefig(graph_img, format='png')
    plt.close()
    graph_img.seek(0)

    # Generate PDF
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.drawString(30, 750, f"Analysis Report for {url}")
    c.drawString(30, 730, f"Meta Description: {meta_desc}")
    c.drawString(30, 710, f"Meta Keywords: {meta_keywords}")
    c.drawString(30, 690, f"Top Words: {', '.join([w for w, _ in common_words])}")

    chart_reader = ImageReader(bar_chart_img)
    graph_reader = ImageReader(graph_img)
    c.drawImage(chart_reader, 30, 480, width=400, height=150)
    c.drawImage(graph_reader, 30, 300, width=400, height=150)

    c.save()
    pdf_buffer.seek(0)

    return send_file(pdf_buffer, download_name='report.pdf', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)