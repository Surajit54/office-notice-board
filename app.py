import random
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session

app = Flask(__name__)
app.secret_key = "office-secret-key"

UPLOAD_FOLDER = "UPLOADS"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- VIEW PDF ----------------
@app.route("/view/<filename>")
def view_pdf(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ---------------- NOTICE LIST (PUBLIC) ----------------
@app.route("/notices")
def notices():
    page = request.args.get("page", 1, type=int)
    per_page = 5

    files = os.listdir(app.config["UPLOAD_FOLDER"])
    pdf_files = []

    for f in files:
        if f.endswith(".pdf"):
            path = os.path.join(app.config["UPLOAD_FOLDER"], f)
            timestamp = os.path.getmtime(path)
            date = datetime.fromtimestamp(timestamp).strftime("%d-%m-%Y")

            pdf_files.append({
                "name": f,
                "date": date,
                "time": timestamp
            })

    # newest first
    pdf_files.sort(key=lambda x: x["time"], reverse=True)

    total = len(pdf_files)
    total_pages = (total + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page
    paginated = pdf_files[start:end]

    return render_template(
        "notices.html",
        notices=paginated,
        page=page,
        total_pages=total_pages
    )
# -------- Latest notices for marquee --------
@app.context_processor
def inject_latest_notices():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    pdfs = []

    for f in files:
        if f.endswith('.pdf'):
            path = os.path.join(app.config['UPLOAD_FOLDER'], f)
            timestamp = os.path.getmtime(path)
            pdfs.append((f, timestamp))

    # newest first
    pdfs.sort(key=lambda x: x[1], reverse=True)

    # only last 5 notices
    latest = [x[0] for x in pdfs[:5]]

    return dict(latest_notices=latest)


# ---------------- LOGIN ----------------
# ---------------- MOBILE LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':
        mobile = request.form['mobile']

        # OTP generate
        otp = str(random.randint(100000,999999))

        session['otp'] = otp
        session['mobile'] = mobile

        print("OTP IS:", otp)   # Terminal এ দেখাবে (SMS এর বদলে)

        return redirect(url_for('verify'))

    return render_template('login.html')
@app.route('/verify', methods=['GET','POST'])
def verify():

    if request.method == 'POST':
        user_otp = request.form['otp']

        if user_otp == session.get('otp'):
            session['user'] = session.get('mobile')
            return redirect(url_for('upload'))

    return render_template('verify.html')



# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))


# ---------------- UPLOAD PAGE ----------------
@app.route('/upload', methods=['GET','POST'])
def upload():

    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        files = request.files.getlist('pdf_files')

        for file in files:
            if file and file.filename.endswith('.pdf'):
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

        return redirect(url_for('notices'))

    return render_template('upload.html')


# ---------------- DELETE FILE ----------------
@app.route('/delete/<filename>')
def delete_file(filename):

    if 'user' not in session:
        return redirect(url_for('login'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    return redirect(url_for('notices'))


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
