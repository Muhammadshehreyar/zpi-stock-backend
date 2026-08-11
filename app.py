import os
from flask import Flask, render_template_string, request, redirect, url_for, session, make_response
import sqlite3, os
from werkzeug.utils import secure_filename
from datetime import datetime
from reportlab.pdfgen import canvas
from io import BytesIO

app = Flask(__name__)
app.secret_key = "zpi_pro_2026"
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    conn = sqlite3.connect('database.db'); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS manufacturers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, manufacturer_id INTEGER, brand TEXT,
        bag_size TEXT, quantity INTEGER, picture_path TEXT,
        FOREIGN KEY(manufacturer_id) REFERENCES manufacturers(id)
    )''')
    c.execute("INSERT OR IGNORE INTO users VALUES (1, 'admin', 'admin123')")
    c.execute("INSERT OR IGNORE INTO manufacturers (name) VALUES ('Gohar Plastics')")
    c.execute("INSERT OR IGNORE INTO manufacturers (name) VALUES ('Al-Madina Bags')")
    conn.commit(); conn.close()
init_db()

CSS = '''<style>
body{font-family:'Segoe UI', Arial; background:#f4f6f9; margin:0;}
.header{background:linear-gradient(135deg,#203a43,#2c5364); color:white; padding:15px 30px; display:flex; justify-content:space-between; align-items:center; box-shadow:0 2px 5px rgba(0,0,0,0.2);}
.logo{width:45px; height:45px; border-radius:50%; vertical-align:middle; margin-right:10px;}
.container{padding:25px; max-width:1200px; margin:auto;}
.card{background:white; padding:25px; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.08); margin-bottom:25px;}
.btn{padding:12px 20px; background:#28a745; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer;}
.btn-blue{background:#007bff;}
.btn-red{background:#dc3545;}
input,select{width:100%; padding:12px; margin:8px 0; border:1px solid #ccc; border-radius:6px; box-sizing:border-box;}
table{width:100%; background:white; border-collapse:collapse; border-radius:8px; overflow:hidden;}
th{background:#203a43; color:white; padding:14px;} td{padding:12px; text-align:center; border-bottom:1px solid #eee;}
img.thumb{width:70px; height:70px; object-fit:cover; border-radius:6px;}
.flex{display:flex; gap:15px;}
</style>'''

LOGIN = CSS + '''<html><head><title>ZPI Login</title></head><body style="background:linear-gradient(135deg,#203a43,#2c5364); display:flex; justify-content:center; align-items:center; height:100vh;">
<div class="card" style="width:350px; text-align:center;">
<img src="{{ url_for('static', filename='logo.png') }}" style="width:90px; height:90px; border-radius:50%; border:3px solid #203a43;" onerror="this.src='https://i.imgur.com/8Km9tLL.png'">
<h2 style="color:#203a43;">Zeeshan Plastic Industry</h2>
<form method="POST"><input name="u" placeholder="Username" required><input name="p" type="password" placeholder="Password" required><button class="btn" style="width:100%;">Login</button></form></div></body></html>'''

DASH = CSS + '''<html><head><title>ZPI Dashboard</title></head><body>
<div class="header">
<div><img src="{{ url_for('static', filename='logo.png') }}" class="logo" onerror="this.src='https://i.imgur.com/8Km9tLL.png'"> <b style="font-size:18px;">ZPI Stock Dashboard</b></div>
<div><a href="/pdf" class="btn btn-blue">📄 Download PDF</a> <a href="/logout" class="btn btn-red">Logout</a></div>
</div>
<div class="container">

<div class="card">
<h3>➕ Add New Manufacturer</h3>
<form method="POST" action="/add_manufacturer" class="flex">
<input type="text" name="mfg_name" placeholder="New Manufacturer Name e.g. Pak Plastics" required style="flex:1;">
<button class="btn btn-blue">Add Manufacturer</button>
</form></div>

<div class="card">
<h3>📦 Add New Stock Entry</h3>
<form method="POST" enctype="multipart/form-data">
<label><b>1. Stock ki Picture - Camera Proof</b></label>
<input type="file" name="pic" accept="image/*" capture="environment" required>

<div class="flex">
<div style="flex:1;"><label><b>2. Manufacturer Select Karo</b></label>
<select name="mfg_id" required><option value="">-- Select --</option>{% for m in manufacturers %}<option value="{{ m[0] }}">{{ m[1] }}</option>{% endfor %}</select></div>
<div style="flex:1;"><label><b>3. Brand Select Karo</b></label>
<select name="brand" required><option>Ittefaq</option><option>Champion</option><option>Sultan</option></select></div>
</div>

<div class="flex">
<div style="flex:1;"><label>Bag Size</label><input type="text" name="size" placeholder="12x15" required></div>
<div style="flex:1;"><label>Quantity</label><input type="number" name="qty" required></div>
<div style="flex:1;"><label>Date</label><input type="date" name="date" value="{{ today }}" required></div>
</div>
<button class="btn" style="width:100%; margin-top:10px;">Save & Add to Dashboard</button>
</form></div>

<div class="card">
<h3>📊 Overall Stock Data</h3>
<table><tr><th>Date</th><th>Manufacturer</th><th>Brand</th><th>Size</th><th>Qty</th><th>Picture Proof</th></tr>
{% for i in data %}<tr>
<td>{{ i[1] }}</td><td><b>{{ i[2] }}</b></td><td>{{ i[3] }}</td><td>{{ i[4] }}</td><td>{{ i[5] }}</td>
<td>{% if i[6] %}<img src="{{ url_for('static', filename=i[6]) }}" class="thumb">{% else %}-{% endif %}</td>
</tr>{% endfor %}</table></div>
</div></body></html>'''

@app.route('/', methods=['GET','POST'])
def login():
    if request.method=='POST':
        if request.form['u']=='admin' and request.form['p']=='admin123':
            session['user']='admin'; return redirect('/dashboard')
    return render_template_string(LOGIN)

@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if 'user' not in session: return redirect('/')
    if request.method=='POST':
        date=request.form['date']; mfg_id=request.form['mfg_id']; brand=request.form['brand']; size=request.form['size']; qty=request.form['qty']
        pic=request.files['pic']; path=None
        if pic: fn=secure_filename(pic.filename); pic.save(os.path.join(app.config['UPLOAD_FOLDER'], fn)); path='uploads/'+fn
        conn=sqlite3.connect('database.db'); c=conn.cursor()
        c.execute("INSERT INTO stock (date,manufacturer_id,brand,bag_size,quantity,picture_path) VALUES (?,?,?,?,?,?)",(date,mfg_id,brand,size,qty,path))
        conn.commit(); conn.close(); return redirect('/dashboard')

    conn=sqlite3.connect('database.db'); c=conn.cursor()
    c.execute("SELECT s.id, s.date, m.name, s.brand, s.bag_size, s.quantity, s.picture_path FROM stock s JOIN manufacturers m ON s.manufacturer_id=m.id ORDER BY s.date DESC")
    data=c.fetchall()
    c.execute("SELECT * FROM manufacturers ORDER BY name")
    manufacturers=c.fetchall(); conn.close()
    return render_template_string(DASH, data=data, manufacturers=manufacturers, today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/add_manufacturer', methods=['POST'])
def add_mfg():
    if 'user' in session:
        name=request.form['mfg_name']
        conn=sqlite3.connect('database.db'); c=conn.cursor()
        c.execute("INSERT OR IGNORE INTO manufacturers (name) VALUES (?)",(name,))
        conn.commit(); conn.close()
    return redirect('/dashboard')

@app.route('/pdf')
def pdf():
    conn=sqlite3.connect('database.db'); c=conn.cursor()
    c.execute("SELECT s.date, m.name, s.brand, s.bag_size, s.quantity FROM stock s JOIN manufacturers m ON s.manufacturer_id=m.id ORDER BY s.date DESC")
    data=c.fetchall(); conn.close()
    buffer=BytesIO(); p=canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold",16); p.drawString(170,800,"Zeeshan Plastic Industry")
    p.setFont("Helvetica",10); p.drawString(50,780,f"Stock Report - {datetime.now().strftime('%d-%m-%Y')}")
    y=750; headers=["Date","Manufacturer","Brand","Size","Qty"]; x=[50,120,250,320,380]
    for i,h in enumerate(headers): p.drawString(x[i],y,h)
    y-=20
    for row in data:
        for i,val in enumerate(row): p.drawString(x[i],y,str(val))
        y-=20; 
        if y<50: p.showPage(); y=800
    p.save(); buffer.seek(0)
    return make_response(buffer.getvalue(),200,{'Content-Type':'application/pdf','Content-Disposition':'attachment; filename=ZPI_Stock_Report.pdf'})

@app.route('/logout')
def out(): session.clear(); return redirect('/')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
