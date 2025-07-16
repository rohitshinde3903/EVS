from flask_mail import Mail, Message

from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'your_secret_key'




# Database setup
DATABASE = 'database.db'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create Voters table
    cursor.execute('''CREATE TABLE IF NOT EXISTS voters (
                    id INTEGER,
                    name VARCHAR(100),
                    class VARCHAR(50),
                    voted INTEGER DEFAULT 0,
                    password INTEGER DEFAULT 0,
                    email VARCHAR(100),
                    PRIMARY KEY (id, email)
                )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS voters_auth (
                        id INTEGER,
                        email TEXT NOT NULL,
                        au_otp TEXT,
                        au_status TEXT,
                        password INTEGER DEFAULT 0,
                        images TEXT,
                        PRIMARY KEY (id, email)
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS positions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL
                    )''')

    # Create Candidates table with image column
    cursor.execute('''CREATE TABLE IF NOT EXISTS candidates (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        class TEXT NOT NULL,
                        position TEXT NOT NULL,
                        votes INTEGER DEFAULT 0,
                        image TEXT)''')

    conn.commit()
    conn.close()

# Home Page (Index Page for Users)
@app.route('/')
def index():
    return render_template('index.html')


# Admin Panel (Dashboard)
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'password':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('admin_login.html')

# Admin Panel (Dashboard)
@app.route('/admin_dashboard')
def admin_panel():
    if not session.get('admin_logged_in'):
        flash('Please log in as Admin to access the dashboard', 'warning')
        return redirect(url_for('admin_login'))
    else:
         conn = get_db_connection()

    # Get total registered voters
         total_voters = conn.execute('SELECT COUNT(*) FROM voters').fetchone()[0]

        # Get total voted
         total_voted = conn.execute('SELECT COUNT(*) FROM voters WHERE voted = 1').fetchone()[0]

        # Calculate not voted
         not_voted = total_voters - total_voted

         conn.close()
    return render_template('admin_dashboard.html',total_voters=total_voters, total_voted=total_voted, not_voted=not_voted)



@app.route('/delete_voter/<int:voter_id>', methods=['POST'])
def delete_voter(voter_id):
    if not session.get('admin_logged_in'):
        flash('Please log in as Admin to delete a voter', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM voters WHERE id = ?', (voter_id,))
    conn.execute('DELETE FROM voters_auth WHERE id = ?', (voter_id,))
    conn.commit()
    conn.close()
    
    flash('Voter deleted successfully', 'success')
    return redirect(url_for('voters'))




@app.route('/voters', methods=['GET', 'POST'])
def voters():
    if not session.get('admin_logged_in'):
        flash('Please log in as Admin to access the candidates page', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    voters = []

    if request.method == 'POST':
        # Get search criteria from form
        search_query = request.form['search_query']
        search_query = f"%{search_query}%"

        # Search in voters table by ID, name, or email
        voters = conn.execute('''
            SELECT * FROM voters
            WHERE id LIKE ? OR name LIKE ? OR email LIKE ?
        ''', (search_query, search_query, search_query)).fetchall()
        
    else:
        # Fetch all voters if no search is performed
        voters = conn.execute('SELECT * FROM voters').fetchall()

    conn.close()
    return render_template('voters.html', voters=voters)


@app.route('/candidates')
def candidates():
    if not session.get('admin_logged_in'):
        flash('Please log in as Admin to access the candidates page', 'warning')
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    candidates = conn.execute('SELECT * FROM candidates').fetchall()
    positions = conn.execute('SELECT * FROM positions').fetchall()
    conn.close()

    return render_template('candidates.html', candidates=candidates, positions=positions)





@app.route('/positions')
def manage_positions():
    if not session.get('admin_logged_in'):
        flash('Please log in as Admin to access the positions page', 'warning')
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    positions = conn.execute('SELECT * FROM positions').fetchall()
    conn.close()

    return render_template('positions.html', positions=positions)

@app.route('/add_position', methods=['POST'])
def add_position():
    if not session.get('admin_logged_in'):
        flash('Please log in as Admin to add positions', 'warning')
        return redirect(url_for('admin_login'))

    position_name = request.form['position']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM positions")

    # Fetch all rows from the executed query
    rows = cursor.fetchall()

    # Extract emails and store them in a list
    name_list = [row[0] for row in rows]
    
    if position_name not in name_list:
        conn.execute('INSERT INTO positions (name) VALUES (?)', (position_name,))
        conn.commit()
        conn.close()
        flash('Position added successfully', 'success')
        return redirect(url_for('manage_positions'))
    else:
        flash('Position already exists', 'warning')
        return redirect(url_for('manage_positions'))


@app.route('/delete_position/<int:position_id>', methods=['POST'])
def delete_position(position_id):
    if not session.get('admin_logged_in'):
        flash('Please log in as Admin to delete positions', 'warning')
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM positions WHERE id = ?', (position_id,))
    conn.commit()
    conn.close()

    flash('Position deleted successfully.', 'success')
    return redirect(url_for('manage_positions'))




@app.route('/delete_candidate/<int:candidate_id>', methods=['POST'])
def delete_candidate(candidate_id):
    if not session.get('admin_logged_in'):
        flash('Please log in as Admin to access the candidates page', 'warning')
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM candidates WHERE id = ?', (candidate_id,))
    conn.commit()
    conn.close()

    flash('Candidate deleted successfully.', 'success')
    return redirect(url_for('candidates'))


# Add Voter logic
@app.route('/add_new_voter', methods=['POST'])
def add_new_voter():
    # Only accessible after logging in
    if not session.get('admin_logged_in'):
        flash('Please log in as Admin to add a voter', 'warning')
        return redirect(url_for('admin_login'))

    # Retrieve form data
    voter_id = request.form['voter_id']
    name = request.form['name']
    class_name = request.form['class']
    email = request.form['email']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch existing emails and IDs
        cursor.execute("SELECT email FROM voters")
        email_list = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT id FROM voters")
        id_list = [row[0] for row in cursor.fetchall()]

        # Check if email or voter_id already exists
        if email in email_list:
            flash("Email is already present! Please use a unique email.", "error")
        elif voter_id in id_list:
            flash("Voter ID already exists! Please use a unique ID.", "error")
        else:
            # Add new voter if no conflicts
            conn.execute(
                'INSERT INTO voters (id, name, class, email) VALUES (?, ?, ?, ?)',
                (voter_id, name, class_name, email)
            )
            conn.execute(
                'INSERT INTO voters_auth (id, email) VALUES (?, ?)',
                (voter_id, email)
            )
            conn.commit()
            flash("Voter added successfully!", "success")
    except sqlite3.IntegrityError as e:
        flash(f"Database Error: {e}", "error")
    except Exception as e:
        flash(f"An unexpected error occurred: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for('voters'))


# Add Candidate logic
@app.route('/add_candidate', methods=['POST'])
def add_candidate():
    # Only accessible after logging in
    if not session.get('admin_logged_in'):
        flash('Please log in as Admin to add a candidate', 'warning')
        return redirect(url_for('admin_login'))

    name = request.form['name']
    class_name = request.form['class']
    position = request.form['position']
    image = request.files['image']
    candidate_id = request.form['candidate_id']

    # Save the image
    image_filename = image.filename
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    image.save(image_path)

    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO candidates (id, name, class, position, image) VALUES (?, ?, ?, ?, ?)',
                     (candidate_id, name, class_name, position, image_filename))
        conn.commit()
        flash('Candidate added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Candidate ID already exists! Please enter a unique ID.', 'error')
    finally:
        conn.close()

    return redirect(url_for('candidates'))

# Start Voting Page
@app.route('/start_voting', methods=['GET', 'POST'])
def start_voting():
    # Check if admin is logged in
    if not session.get('admin_logged_in'):
        flash('Please log in as Admin to access this page', 'warning')
        return redirect(url_for('admin_login'))

    voter_info = None  # Ensure voter_info is defined

    if request.method == 'POST':
        voter_id = request.form['voter_id']
        password = request.form['password']

        conn = get_db_connection()
        voter = conn.execute('SELECT * FROM voters WHERE id = ?', (voter_id,)).fetchone()
        voters = conn.execute('SELECT * FROM voters_auth WHERE id = ?', (voter_id,)).fetchone()

        if voter is None:
            flash('Voter not found or not registered!', 'error')
            conn.close()
            return redirect(url_for('start_voting'))

        if voters['password'] != password:
            flash('Wrong Password!', 'error')
            conn.close()
            return redirect(url_for('start_voting'))

        if voter['voted'] == 1:
            flash('You have already voted!', 'error')
            conn.close()
            return redirect(url_for('start_voting'))


        voter_info = voter  # Store voter info to pass to the template

        # Fetch all candidates
        candidates = conn.execute('SELECT * FROM candidates').fetchall()
        conn.close()

        return render_template('start_voting.html', voter_info=voter_info, candidates=candidates)

    return render_template('start_voting.html', voter_info=voter_info)






import random

@app.route('/send_mail', methods=['GET', 'POST'])
def send_mail(voter_id, email):
    conn = get_db_connection()

    # Fetch voter details
    voter = conn.execute('SELECT * FROM voters_auth WHERE id = ?', (voter_id,)).fetchone()

    # Check if voter exists and email matches
    if voter is None or voter['email'] != email:
        flash('Voter not found or not registered! Check email and ID')
        conn.close()
        return redirect(url_for('add_new_voter'))

    # Generate OTP
    au_otp = random.randint(1000, 9999)  # Adjusted range to 9999 for a 4-digit OTP

    # Prepare email
    msg = MIMEText(f"Your OTP is: {au_otp}")
    msg['Subject'] = "Your OTP Code for the registration process."
    msg['From'] = 'stoneswebservices@gmail.com'  # Replace with your email
    msg['To'] = voter['email']

    # Send email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('stoneswebservices@gmail.com', 'asav ftnn lwyo ekra')  # Use App Password
            server.sendmail(msg['From'], [msg['To']], msg.as_string())

        # Update OTP in the database
        conn.execute('UPDATE voters_auth SET au_otp = ? WHERE id = ?', (au_otp, voter_id))
        conn.commit()

        flash('OTP sent to your email.', 'success')
        return True  # Return True if everything was successful
    except Exception as e:
        flash('Failed to send OTP. Please try again later.', 'error')
        print(f"Error: {e}")  # Log the error for debugging
        return False  # Return False if there was an error
    finally:
        conn.close()




@app.route('/register_voter', methods=['GET', 'POST'])
def register_voter():


    if request.method == 'POST':
        voter_id = request.form['voter_id']
        email = request.form['email']
        

        result = send_mail(voter_id, email)

        # Check if send_mail returned True
        if result == True:
            return render_template('otp1.html')

        flash('error', 'danger')
        return render_template('register.html')

    return render_template('register.html')



@app.route('/validate_voter', methods=['GET', 'POST'])
def validate_voter():

    if request.method == 'POST':
        voter_id = request.form['voter_id']
        otp = request.form['otp']
        
        try:
            conn = get_db_connection()
            voter = conn.execute('SELECT * FROM voters_auth WHERE id = ?', (voter_id,)).fetchone()

            if voter['au_otp'] == otp:
                conn.execute('UPDATE voters_auth SET au_status = ? WHERE id = ?', ('active', voter_id))
                conn.commit()
                conn.close()
                return render_template('create_password.html')
            flash('Invalid OTP', 'danger')
            return render_template("otp1.html",)
        except Exception as e:
            flash('Invalid OTP or id. Please try again.', 'error')
        conn.close()
    return render_template('otp1.html',)


@app.route('/create_password', methods=['GET', 'POST'])
def create_password():
    if request.method == 'POST':
        voter_id = request.form['voter_id']
        password = request.form['password']

        conn = get_db_connection()
        voter = conn.execute('SELECT * FROM voters_auth WHERE id = ?', (voter_id,)).fetchone()

        if voter is None:
            flash('Voter not found!', 'error')
            return redirect(url_for('create_password'))

        # Update password in the database
        conn.execute('UPDATE voters_auth SET password = ? WHERE id = ?', (password, voter_id))
        conn.execute('UPDATE voters SET password = 1 WHERE id = ?', (voter_id,))
        conn.commit()

        # Send confirmation email
        voters = conn.execute('SELECT * FROM voters WHERE id = ?', (voter_id,)).fetchone()
        voter_name = voters['name']
        to_email = voter['email']
        subject = "Vote Confirmation"
        body = f"Hello {voter_name},\n\nYou have successfully created your password and your password is *******{password}*******. Thank you for participating!"

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = 'stoneswebservices@gmail.com'  # Replace with your email
        msg['To'] = to_email

        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login('stoneswebservices@gmail.com', 'asav ftnn lwyo ekra')  # Replace with your email and password
                server.sendmail(msg['From'], [msg['To']], msg.as_string())

            flash('Password Created Successfully and Email Sent', 'success')
            conn.close()
            return redirect(url_for('index'))  # Redirect to home or index page after success
        except Exception as e:
            flash(f"Failed to send email: {e}", 'error')

        conn.close()

    return render_template('create_password.html')

import requests

# Function to send email notification
def send_email(to_email, voter_name, candidate_name):
    subject = "Vote Confirmation"
    body = f"Hello {voter_name},\n\nYou have successfully cast your vote to {candidate_name}. Thank you for participating!"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'stoneswebservices@gmail.com'  # Replace with your email
    msg['To'] = to_email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('stoneswebservices@gmail.com', 'asav ftnn lwyo ekra')  # Replace with your email and password
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

@app.route('/vote', methods=['POST'])
def vote():
    if request.method == 'POST':
        voter_id = request.form['voter_id']

        # Get database connection
        conn = get_db_connection()

        # Fetch voter information
        voter = conn.execute('SELECT * FROM voters WHERE id = ?', (voter_id,)).fetchone()

        if voter and voter['voted'] == 0:
            # Initialize flag to track if all votes are successful
            all_votes_successful = True

            # Loop through each selected candidate by category
            for key, candidate_id in request.form.items():
                if key.startswith('candidate_id_'):
                    # Fetch candidate information
                    candidate = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
                    if candidate:
                        # Update the vote count for the candidate
                        conn.execute('UPDATE candidates SET votes = votes + 1 WHERE id = ?', (candidate_id,))
                    else:
                        all_votes_successful = False
                        flash(f'Invalid candidate selected for {key}', 'error')

            # Update voter's status to "voted" if all votes were successful
            if all_votes_successful:
                conn.execute('UPDATE voters SET voted = 1 WHERE id = ?', (voter_id,))

                # Commit changes
                conn.commit()

                # Get voter's email
                voter_email = voter['email']  # Assuming the email column exists

                # Send email notification to the voter
                if send_email(voter_email, voter['name'], "All Selected Candidates"):
                    flash('Vote recorded successfully. A confirmation email has been sent to your email.', 'success')
                else:
                    flash('Vote recorded successfully, but failed to send email notification.', 'warning')
            else:
                flash('Failed to record some votes. Please try again.', 'error')
        else:
            flash('Invalid voter or you have already voted!', 'error')

        # Close the connection
        conn.close()

        return redirect(url_for('start_voting'))

    return redirect(url_for('start_voting'))

# About Page
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/back')
def back():
    return redirect(url_for('admin_panel'))





@app.route('/declare_winners')
def declare_winners():
    conn = get_db_connection()

    # Fetch all categories from the database (assuming you have categories in the 'candidates' table)
    categories = conn.execute('SELECT DISTINCT position FROM candidates').fetchall()

    winners = []

    # Loop through each category and find the winner and second place
    for category in categories:
        position = category['position']

        # Query to get the top two candidates in the current category based on votes
        candidates = conn.execute('''
            SELECT id, name, votes 
            FROM candidates 
            WHERE position = ?
            ORDER BY votes DESC
            LIMIT 2
        ''', (position,)).fetchall()

        if len(candidates) > 0:
            winner = candidates[0]  # Candidate with the highest votes
            second_place = candidates[1] if len(candidates) > 1 else None  # Second candidate (if exists)
            margin = winner['votes'] - (second_place['votes'] if second_place else 0)  # Margin of victory

            winners.append({
                'position': position,
                'winner_name': winner['name'],
                'winner_votes': winner['votes'],
                'margin': margin,
                'second_name': second_place['name'] if second_place else 'No other candidate',
                'second_votes': second_place['votes'] if second_place else 0
            })

    conn.close()

    return render_template('declare_winners.html', winners=winners)

@app.route('/voted')
def voted():
    conn = get_db_connection()

    voters_voted = conn.execute('SELECT * FROM voters').fetchall()

    conn.close()
    return render_template('voted.html', voters_voted=voters_voted) 



# Run the app and initialize the database
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
