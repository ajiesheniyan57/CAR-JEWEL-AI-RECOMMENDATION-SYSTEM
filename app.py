from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

df = None

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

# =========================
# MODERN UI (TOP NAV + CLEAN DESIGN)
# =========================
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Car Jewel AI</title>

<meta name="viewport" content="width=device-width, initial-scale=1">

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

<style>
body {
    background: #f4f6f9;
    font-size: 16px;
}

.navbar {
    background: #0d6efd;
}

.card {
    border-radius: 12px;
}

.section-title {
    font-weight: 600;
    margin-bottom: 10px;
}

/* Mobile improvements */
@media (max-width: 768px) {
    h3, .section-title {
        text-align: center;
    }

    button {
        font-size: 18px;
    }
}
</style>

</head>

<body>

<!-- NAVBAR -->
<nav class="navbar navbar-dark px-3">
    <span class="navbar-brand">🚗 Car Jewel AI</span>
</nav>

<div class="container-fluid p-3">

<div class="row g-3">

<!-- OWNER PANEL -->
<div class="col-12 col-lg-4">
<div class="card p-3 shadow-sm">

<div class="section-title text-center">👨‍💼 Owner Panel</div>

<input id="username" class="form-control mb-2" placeholder="Username">
<input id="password" class="form-control mb-2" type="password" placeholder="Password">

<button class="btn btn-primary w-100" onclick="login()">Login</button>

<div id="adminSection" style="display:none;">
<hr>
<input type="file" id="file" class="form-control mb-2">
<button class="btn btn-success w-100" onclick="upload()">Upload Dataset</button>
</div>

</div>
</div>

<!-- CUSTOMER PANEL -->
<div class="col-12 col-lg-8">
<div class="card p-3 shadow-sm">

<div class="section-title text-center">👤 Customer Preferences</div>

<div class="row g-2">

<div class="col-12 col-md-4">
<label>Interior</label>
<select id="interior" class="form-select"></select>
</div>

<div class="col-12 col-md-4">
<label>Exterior</label>
<select id="exterior" class="form-select"></select>
</div>

<div class="col-12 col-md-4">
<label>Style</label>
<select id="style" class="form-select"></select>
</div>

</div>

<div class="row mt-3 g-2">

<div class="col-12 col-md-6">
<label>Budget (₹)</label>
<input id="price" class="form-control" type="number" value="500">
</div>

<div class="col-12 col-md-6">
<label>No. of Recommendations</label>
<input id="top_n" class="form-control" type="number" value="5" min="1">
</div>

</div>

<button class="btn btn-dark w-100 mt-3" onclick="recommend()">Get Recommendations</button>

<hr>

<div class="section-title text-center">Results</div>
<ul id="results" class="list-group"></ul>

</div>
</div>

</div>
</div>

<script>

let user = "";

// LOGIN
function login() {
    fetch("/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            username: document.getElementById("username").value,
            password: document.getElementById("password").value
        })
    })
    .then(res => {
        if (!res.ok) throw "Login failed";
        return res.json();
    })
    .then(() => {
        alert("Login Success");
        user = document.getElementById("username").value;
        document.getElementById("adminSection").style.display = "block";
    })
    .catch(() => alert("Invalid login"));
}

// UPLOAD
function upload() {
    const file = document.getElementById("file").files[0];

    if (!file) return alert("Select file");
    if (!user) return alert("Login first");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("username", user);

    fetch("/upload", {
        method: "POST",
        body: formData
    })
    .then(res => res.text())
    .then(msg => {
        alert(msg);
        loadOptions();
    });
}

// LOAD OPTIONS
function loadOptions() {
    fetch("/get-options")
    .then(res => res.json())
    .then(data => {

        if (data.error) return;

        const i = document.getElementById("interior");
        const e = document.getElementById("exterior");
        const s = document.getElementById("style");

        i.innerHTML = "";
        e.innerHTML = "";
        s.innerHTML = "";

        data.interiors.forEach(v => i.innerHTML += `<option>${v}</option>`);
        data.exteriors.forEach(v => e.innerHTML += `<option>${v}</option>`);
        data.styles.forEach(v => s.innerHTML += `<option>${v}</option>`);
    });
}

// RECOMMEND
function recommend() {
    fetch("/recommend", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            interior: document.getElementById("interior").value,
            exterior: document.getElementById("exterior").value,
            style: document.getElementById("style").value,
            price: document.getElementById("price").value,
            top_n: document.getElementById("top_n").value
        })
    })
    .then(res => res.json())
    .then(data => {

        const results = document.getElementById("results");
        results.innerHTML = "";

        if (data.error) {
            results.innerHTML = "<li class='list-group-item'>" + data.error + "</li>";
            return;
        }

        data.forEach(item => {
            results.innerHTML += `
            <li class='list-group-item d-flex justify-content-between'>
                <span>${item.Product}</span>
                <span>₹${item.Price} | ⭐ ${item.Rating}</span>
            </li>`;
        });
    });
}

window.onload = loadOptions;

</script>

</body>
</html>
"""

# =========================
# ROUTES
# =========================

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if data['username'] == ADMIN_USERNAME and data['password'] == ADMIN_PASSWORD:
        return jsonify({"status": "ok"})
    return jsonify({"status": "fail"}), 401


@app.route('/upload', methods=['POST'])
def upload():
    global df

    if request.form.get("username") != ADMIN_USERNAME:
        return "Unauthorized", 403

    file = request.files.get("file")
    if not file:
        return "No file uploaded", 400

    df = pd.read_excel(file)

    required = ['Product','Interior','Exterior','Style','Price','Stock','Rating']
    for col in required:
        if col not in df.columns:
            return f"Missing column: {col}", 400

    return "✅ Dataset uploaded successfully"


@app.route('/get-options')
def options():
    if df is None:
        return jsonify({"error": "Upload dataset first"})

    return jsonify({
        "interiors": df['Interior'].unique().tolist(),
        "exteriors": df['Exterior'].unique().tolist(),
        "styles": df['Style'].unique().tolist()
    })


@app.route('/recommend', methods=['POST'])
def recommend_api():

    if df is None:
        return jsonify({"error": "Upload dataset first"})

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
    app.run(debug=True)
