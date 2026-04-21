from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

df = None

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

# ---------------- HOME (FIXED) ----------------
@app.route('/')
def home():
    return render_template("login.html")   # ✅ FIXED


# ---------------- PAGES ----------------
@app.route('/owner')
def owner_page():
    return render_template("owner.html")

@app.route('/customer')
def customer_page():
    return render_template("customer.html")


# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json

    if data['username'] == ADMIN_USERNAME and data['password'] == ADMIN_PASSWORD:
        return jsonify({"role": "owner"})
    else:
        return jsonify({"role": "customer"})


# ---------------- UPLOAD ----------------
@app.route('/upload', methods=['POST'])
def upload():
    global df

    if request.form.get("username") != ADMIN_USERNAME:
        return "Unauthorized", 403

    file = request.files.get("file")
    if not file:
        return "No file uploaded", 400

    try:
        df = pd.read_excel(file)
    except Exception as e:
        return f"Error reading file: {e}", 400

    # Validate columns
    required = ['Product','Interior','Exterior','Style','Price','Stock','Rating']
    for col in required:
        if col not in df.columns:
            return f"Missing column: {col}", 400

    return "✅ Dataset uploaded successfully"


# ---------------- OPTIONS ----------------
@app.route('/get-options')
def options():
    if df is None:
        return jsonify({"error": "Upload dataset first"})

    return jsonify({
        "interiors": df['Interior'].dropna().unique().tolist(),
        "exteriors": df['Exterior'].dropna().unique().tolist(),
        "styles": df['Style'].dropna().unique().tolist()
    })


# ---------------- RECOMMEND ----------------
@app.route('/recommend', methods=['POST'])
def recommend():
    global df

    if df is None:
        return jsonify({"error": "Upload dataset first"})

    data = request.json
    user_price = float(data['price'])
    top_n = int(data.get('top_n', 5))

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

    df['score'] = scores
    result = df.sort_values(by='score', ascending=False).head(top_n)

    return jsonify(result.to_dict(orient="records"))


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
