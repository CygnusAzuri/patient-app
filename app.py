from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2  # Changed from mysql.connector to psycopg2
import pandas as pd
from waitress import serve
import secrets
from dotenv import load_dotenv
import os
from flask import send_file
import io

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# PostgreSQL Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        return conn
    except psycopg2.Error as err:
        print(f"Error: {err}")
        flash("Database connection failed.", "error")
        return None

# Predefined credentials for the doctor
DOCTOR_USERNAME = "doctor"
DOCTOR_PASSWORD = "password123"

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == DOCTOR_USERNAME and password == DOCTOR_PASSWORD:
            session['logged_in'] = True
            flash('Login Successful!', 'success')
            return redirect(url_for('patient_list'))
        else:
            flash("Invalid username or password.", "error")
            return redirect(url_for('login'))
    return render_template('auth.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route("/", methods=["GET"])
def home():
    if session.get('logged_in'):
        return redirect(url_for('patient_list'))  # Redirect to the patient dashboard if logged in
    return redirect(url_for('login'))  # Redirect to login if not logged in

# Route to list all patients
@app.route('/patients', methods=['GET'])
def patient_list():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()  # No need to use dictionary=True here for PostgreSQL
    cursor.execute('SELECT * FROM patients')
    patients = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('patient_list.html', patients=patients)

# Route to view patient details
@app.route('/patient/<int:id>', methods=['GET'])
def view_patient(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM patients WHERE id = %s', (id,))
    patient = cursor.fetchone()
    cursor.close()
    conn.close()

    if not patient:
        flash("Patient not found.", "error")
        return redirect(url_for('patient_list'))

    return render_template('patient_view.html', patient=patient)

# Route to create or update a patient
@app.route('/patient/form', methods=['GET', 'POST'])
@app.route('/patient/form/<int:id>', methods=['GET', 'POST'])
def patient_form(id=None):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # If editing a patient
    if id:
        cursor.execute('SELECT * FROM patients WHERE id = %s', (id,))
        patient = cursor.fetchone()

        if not patient:
            flash("Patient not found.", "error")
            return redirect(url_for('patient_list'))

        if request.method == 'POST':
            name = request.form['name']
            age = request.form['age']
            gender = request.form['gender']
            contact = request.form['contact']
            kyc = request.form['kyc']
            concern = request.form['concern']

            cursor.execute(''' 
                UPDATE patients SET name=%s, age=%s, gender=%s, contact=%s, kyc=%s, concern=%s 
                WHERE id=%s
            ''', (name, age, gender, contact, kyc, concern, id))
            conn.commit()
            flash("Patient updated successfully!", "success")
            return redirect(url_for('patient_list'))

        return render_template('patient_form.html', patient=patient)

    # If creating a new patient
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        contact = request.form['contact']
        kyc = request.form['kyc']
        concern = request.form['concern']

        cursor.execute('SELECT * FROM patients WHERE contact = %s', (contact,))
        existing_patient = cursor.fetchone()

        if existing_patient:
            flash("A patient with this contact already exists.", "error")
        else:
            cursor.execute(''' 
                INSERT INTO patients (name, age, gender, contact, kyc, concern) 
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (name, age, gender, contact, kyc, concern))
            conn.commit()
            flash("Patient added successfully!", "success")
            return redirect(url_for('patient_list'))

    return render_template('patient_form.html', patient={})

@app.route('/export', methods=['GET'])
def export_data():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM patients')
    patients = cursor.fetchall()
    cursor.close()
    conn.close()

    df = pd.DataFrame(patients, columns=['ID', 'Name', 'Age', 'Gender', 'Contact', 'KYC', 'Concern'])
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return send_file(output, attachment_filename="patient_data.xlsx", as_attachment=True)

@app.route('/patient/delete/<int:id>', methods=['GET', 'POST'])
def patient_delete(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete the patient record with the given ID
    cursor.execute('DELETE FROM patients WHERE id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Patient deleted successfully!', 'success')
    return redirect(url_for('patient_list'))

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
