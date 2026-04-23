from flask import Flask, render_template_string, request, redirect, url_for, session
from collections import Counter
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

# ---------------------------
# LOAD WORDS
# ---------------------------
def load_words(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [w.strip().lower() for w in f if len(w.strip()) == 5]

all_words = load_words("koncnebesede.txt")

# ---------------------------
# FILTER
# ---------------------------
def filter_words(words, guess, result):
    new_words = []

    for word in words:
        ok = True

        for i in range(5):
            if result[i] == "z":  # green
                if word[i] != guess[i]:
                    ok = False
                    break

            elif result[i] == "r":  # yellow
                if guess[i] not in word or word[i] == guess[i]:
                    ok = False
                    break

            elif result[i] == "c":  # gray
                if guess[i] in word:
                    ok = False
                    break

        if ok:
            new_words.append(word)

    return new_words

# ---------------------------
# SCORING
# ---------------------------
def compute_global_frequency(all_words):
    counter = Counter()
    for w in all_words:
        counter.update(set(w))
    return counter

freq = compute_global_frequency(all_words)

def score_word(word, freq, penalty=0.5):
    counts = Counter(word)
    score = 0

    for c in set(word):
        score += freq[c]

    for c, count in counts.items():
        if count > 1:
            score -= (count - 1) * freq[c] * penalty

    return score

def best_10_words(candidates, freq):
    scored = [(w, score_word(w, freq)) for w in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:10]

# ---------------------------
# HTML
# ---------------------------
HTML = """
<!doctype html>
<html>
<head>
    <title>Wordle Solver</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial;
            max-width: 700px;
            margin: auto;
            padding: 20px;
            background: #121213;
            color: white;
        }

        input, button {
            padding: 10px;
            margin: 5px;
            border-radius: 5px;
            border: none;
        }

        input {
            width: 120px;
        }

        button {
            cursor: pointer;
            background: #538d4e;
            color: white;
        }

        .reset-btn {
            background: #b59f3b;
        }

        ul {
            list-style: none;
            padding: 0;
        }

        li {
            padding: 4px 0;
        }
    </style>
</head>
<body>
    <h1>Wordle Solver</h1>

    <p><b>Možnih besed:</b> {{ count }}</p>

    <form method="post">
        <input name="guess" placeholder="Beseda" maxlength="5" required>
        <input name="result" placeholder="z/r/c" maxlength="5" required>
        <button type="submit">Potrdi</button>
    </form>

    <form action="/reset" method="post">
        <button class="reset-btn" type="submit">Nova beseda</button>
    </form>

    <h2>Top 10 predlogov</h2>
    <ul>
    {% for w, s in top10 %}
        <li>{{ w }} ({{ '%.2f'|format(s) }})</li>
    {% endfor %}
    </ul>

    <h2>Možnosti</h2>
    <p>{{ words|join(', ') }}</p>
</body>
</html>
"""

# ---------------------------
# ROUTES
# ---------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    history = session.get("history", [])

    if request.method == "POST":
        guess = request.form["guess"].lower()
        result = request.form["result"].lower()

        if len(guess) == 5 and len(result) == 5:
            history.append((guess, result))
            session["history"] = history

    # recompute from history
    moznosti = all_words.copy()
    for guess, result in history:
        moznosti = filter_words(moznosti, guess, result)

    top10 = best_10_words(moznosti, freq)

    return render_template_string(
        HTML,
        count=len(moznosti),
        top10=top10,
        words=moznosti[:20]
    )

@app.route("/reset", methods=["POST"])
def reset():
    session["history"] = []
    return redirect(url_for("index"))

# ---------------------------
# RUN
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)