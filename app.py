from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# Load dataset
try:
    df = pd.read_excel("data.xlsx")
except:
    df = None

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if data['username'] == ADMIN_USERNAME and data['password'] == ADMIN_PASSWORD:
        return jsonify({"status": "ok"})
    return jsonify({"status": "fail"}), 401

@app.route('/get-options')
def options():
    if df is None:
        return jsonify({"error": "Dataset not loaded"})
    return jsonify({
        "interiors": df['Interior'].unique().tolist(),
        "exteriors": df['Exterior'].unique().tolist(),
        "styles": df['Style'].unique().tolist()
    })

@app.route('/recommend', methods=['POST'])
def recommend():
    if df is None:
        return jsonify({"error": "Dataset not loaded"})

    data = request.json
    user_price = float(data['price'])
    top_n = min(int(data.get('top_n', 5)), len(df))

    scores = []
    for _, row in df.iterrows():
        score = 0
        if row['Interior'] == data['interior']:
            score += 3
        if row['Exterior'] == data['exterior']:
            score += 3
        if row['Style'] == data['style']:
            score += 2

        price_diff = abs(row['Price'] - user_price)
        score += max(0, 4 - (price_diff / user_price) * 4)
        score += (row['Rating'] / 5) * 2

        scores.append(score)

    df['final_score'] = scores
    results = df.sort_values(by='final_score', ascending=False).head(top_n)

    return jsonify(results.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
