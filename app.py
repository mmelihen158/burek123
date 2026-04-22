# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 01:22:58 2026

@author: korisnik
"""

from flask import Flask, render_template_string, request, redirect, url_for, session
from collections import Counter
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')

# ---------------------------
# LOAD WORDS
# ---------------------------
def load_words(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return [w.strip().lower() for w in f if len(w.strip()) == 5]

all_words = load_words('koncnebesede.txt')

# ---------------------------
# FILTER
# ---------------------------
def filter_words(words, guess, result):
    new_words = []
    for word in words:
        ok = True
        for i in range(5):
            if result[i] == 'z':
                if word[i] != guess[i]:
                    ok = False
                    break
            elif result[i] == 'r':
                if guess[i] not in word or word[i] == guess[i]:
                    ok = False
                    break
            elif result[i] == 'c':
                if guess[i] in word:
                    ok = False
                    break
        if ok:
            new_words.append(word)
    return new_words

# ---------------------------
# SCORE
# ---------------------------
def compute_global_frequency(all_words):
    counter = Counter()
    for w in all_words:
        counter.update(set(w))
    return counter

freq = compute_global_frequency(all_words)

def score_word(word, freq, penalty=0.5):
    counts = Counter(word)
    score = sum(freq[c] for c in set(word))
    for c, count in counts.items():
        if count > 1:
            score -= (count - 1) * freq[c] * penalty
    return score


def best_10_words(candidates, freq):
    scored = [(w, score_word(w, freq)) for w in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:10]

HTML = '''
<!doctype html>
<html>
<head>
<title>Wordle Solver</title>
<style>
body { font-family: Arial; max-width: 700px; margin: auto; padding: 20px; }
input, button { padding: 10px; margin: 5px; }
button { cursor:pointer; }
</style>
</head>
<body>
<h1>Wordle Solver</h1>
<p>Možnih besed: {{ count }}</p>
<form method="post">
    <input name="guess" placeholder="Beseda" maxlength="5" required>
    <input name="result" placeholder="z/r/c" maxlength="5" required>
    <button type="submit">Potrdi</button>
</form>
<form action="/reset" method="post">
    <button type="submit">Nova beseda</button>
</form>
<h2>Top 10 predlogov</h2>
<ul>
{% for w,s in top10 %}
<li>{{ w }} ({{ '%.2f'|format(s) }})</li>
{% endfor %}
</ul>
<h2>Možnosti</h2>
<p>{{ words }}</p>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'moznosti' not in session:
        session['moznosti'] = all_words

    if request.method == 'POST':
        guess = request.form['guess'].lower()
        result = request.form['result'].lower()
        session['moznosti'] = filter_words(session['moznosti'], guess, result)

    moznosti = session['moznosti']
    top10 = best_10_words(moznosti, freq)
    return render_template_string(HTML, count=len(moznosti), top10=top10, words=moznosti[:20])

@app.route('/reset', methods=['POST'])
def reset():
    session['moznosti'] = all_words
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
