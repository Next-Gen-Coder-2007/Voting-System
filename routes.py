from flask import render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
from datetime import datetime, date
from faker import Faker
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import random
db = SQLAlchemy()

fake = Faker()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '123456789'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voting.db'
    app.config['UPLOAD_FOLDER'] = 'static/uploads'

    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app

app = create_app()

from werkzeug.security import generate_password_hash, check_password_hash

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    dob = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    address_lane1 = db.Column(db.String(100), nullable=False)
    address_lane2 = db.Column(db.String(100))
    district = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    phone_no = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.String(200))
    voter_id = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    has_voted = db.Column(db.Boolean, default=False)  # New variable

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    party_name = db.Column(db.String(80), nullable=False)
    party_symbol = db.Column(db.String(200))
    candidate_id = db.Column(db.String(20), unique=True, nullable=False)
    def set_password(self, password):
        self.password = generate_password_hash(password)


class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    election_going = db.Column(db.Boolean, default=True)
    candidates = db.relationship('Candidate', secondary='election_candidate', backref='elections')

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('voter.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)

election_candidate = db.Table('election_candidate',
    db.Column('election_id', db.Integer, db.ForeignKey('election.id'), primary_key=True),
    db.Column('candidate_id', db.Integer, db.ForeignKey('candidate.id'), primary_key=True)
)
# Configure upload folder and max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB max size

# Allowed extensions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    """Check if the file has a valid extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']

        # If no file is selected
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # Check if the file is allowed
        if file and allowed_file(file.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            flash('File successfully uploaded')
            return redirect(url_for('upload_file'))

        else:
            flash('Invalid file format. Please upload a .jpg, .jpeg, .png, or .gif file.')
            return redirect(request.url)
@app.route('/')
def home():
    current_time = datetime.now()
    # Check if any election is currently ongoing
    is_election = Election.query.filter(
        Election.start_time <= current_time,
        Election.end_time >= current_time,
        Election.election_going == True
    ).first() is not None

    return render_template('home.html', is_election=is_election)

@app.route('/generate-dummy-data')
def generate_dummy_data():
    # Generate 50 dummy voters
    for i in range(1, 501):
        voter_id = f"VOTER{i}"
        name = fake.name()
        username = f"user{i}"
        dob = fake.date_of_birth(minimum_age=18, maximum_age=90)
        age = datetime.now().year - dob.year
        gender = random.choice(['Male', 'Female', 'Other'])
        address_lane1 = fake.street_address()
        address_lane2 = fake.secondary_address()
        district = fake.city()
        state = fake.state()
        phone_no = fake.phone_number()
        email = fake.email()
        password = generate_password_hash("password123")
        photo_filename = f"{voter_id}.jpg"  # Dummy filename; you can copy a sample image for each if needed

        voter = Voter(
            voter_id=voter_id,
            name=name,
            username=username,
            dob=dob,
            age=age,
            gender=gender,
            address_lane1=address_lane1,
            address_lane2=address_lane2,
            district=district,
            state=state,
            phone_no=phone_no,
            email=email,
            password=password,
            photo=photo_filename
        )
        db.session.add(voter)

    # Generate 5 dummy candidates
    party_names = ['Unity Party', 'Freedom Front', 'Progressive Alliance', 'Justice League', 'Green Earth']
    for i in range(1, 6):
        candidate_id = f"CAND{i}"
        name = fake.name()
        party_name = party_names[i - 1]
        symbol_filename = f"{candidate_id}.png"  # Dummy filename

        candidate = Candidate(
            candidate_id=candidate_id,
            name=name,
            party_name=party_name,
            party_symbol=symbol_filename
        )
        db.session.add(candidate)
    
    db.session.commit()
    return "Dummy voters and candidates generated!"

@app.route('/welcome')
def welcome():
    election = Election.query.filter_by(election_going=True).first()
    return render_template('welcome.html', election=election)

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/election_results/<int:election_id>')
def view_election_results(election_id):
    # Get election
    election = Election.query.get_or_404(election_id)

    # Get all candidates for that election using the relationship
    candidates = election.candidates

    # Count votes for each candidate
    results = []
    for candidate in candidates:
        vote_count = Vote.query.filter_by(candidate_id=candidate.id, election_id=election.id).count()
        results.append({'candidate': candidate, 'votes': vote_count})

    # Sort by vote count (optional)
    results = sorted(results, key=lambda x: x['votes'], reverse=True)

    return render_template('election_results.html', election=election, results=results)

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    current_time = datetime.now()
    election = Election.query.filter(Election.start_time <= current_time, Election.end_time >= current_time,  Election.election_going == True).first()
    return render_template('admin_dashboard.html',election = election)

@app.route('/voter-login', methods=['GET', 'POST'])
def voter_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        voter = Voter.query.filter_by(username=username).first()
        if voter and check_password_hash(voter.password, password):
            session['voter_id'] = voter.id
            return redirect(url_for('voter_profile'))
    return render_template('voter_login.html')

@app.route('/voter_dashboard')
def voter_dashboard():
    if 'voter_id' not in session:
        return redirect(url_for('voter_login'))
    election = Election.query.filter_by(election_going=True).order_by(Election.id.desc()).first()
    candidates = election.candidates if election else []
    return render_template('voter_dashboard.html', election=election, candidates=candidates)

def get_loggedin_voter():
    voter_id = session.get('voter_id')
    if not voter_id:
        return None
    return Voter.query.get(voter_id)

@app.route('/voter_profile')
def voter_profile():
    voter = get_loggedin_voter()
    if not voter:
        return redirect(url_for('voter_login'))  # Redirect if not logged in

    current_time = datetime.now()
    election = Election.query.filter(Election.start_time <= current_time, Election.end_time >= current_time,  Election.election_going == True).first()
    return render_template('voter_profile.html', voter=voter, election=election)

@app.route('/cast-vote', methods=['POST'])
def cast_vote():
    if 'voter_id' not in session:
        return redirect(url_for('voter_login'))
    voter_id = session['voter_id']
    candidate_id = request.form['candidate']
    election = Election.query.filter_by(election_going=True).order_by(Election.id.desc()).first()
    if election:
        voter = Voter.query.get(voter_id)
        if voter.has_voted:
            flash('You have already voted in this election.', 'error')
        else:
            new_vote = Vote(voter_id=voter_id, candidate_id=candidate_id, election_id=election.id)
            db.session.add(new_vote)
            voter.has_voted = True
            db.session.commit()
            flash('Vote cast successfully!', 'success')
    return redirect(url_for('voter_profile'))

@app.route('/results')
def results():
    election = Election.query.filter_by(election_going=True).order_by(Election.id.desc()).first()
    results = {}
    if election:
        for candidate in election.candidates:
            results[candidate.name] = Vote.query.filter_by(candidate_id=candidate.id, election_id=election.id).count()
    return render_template('results.html', results=results)

@app.route('/voter-management')
def voter_management():
    return render_template('voter_management.html')

@app.route('/candidate-management')
def candidate_management():
    return render_template('candidate_management.html')

@app.route('/election-management')
def election_management():
    elections = Election.query.order_by(Election.start_time.desc()).all()
    return render_template('election_management.html', elections=elections)

@app.route('/add-voter', methods=['GET', 'POST'])
def add_voter():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        dob = datetime.strptime(request.form['dob'], '%Y-%m-%d')
        age = request.form['age']
        gender = request.form['gender']
        address_lane1 = request.form['address_lane1']
        address_lane2 = request.form['address_lane2']
        district = request.form['district']
        state = request.form['state']
        phone_no = request.form['phone_no']
        email = request.form['email']
        photo = request.files['photo']
        password = request.form['password']
        
        voter_id = f"VOTER{len(Voter.query.all()) + 1}"

        # Save photo using voter_id as filename
        filename = None
        if photo and photo.filename != '':
            ext = photo.filename.rsplit('.', 1)[1].lower()
            filename = f"{voter_id}.{ext}"
            upload_path = os.path.join('static', 'uploads')
            os.makedirs(upload_path, exist_ok=True)
            photo.save(os.path.join(upload_path, filename))

        hashed_password = generate_password_hash(password)

        new_voter = Voter(
            name=name,
            username=username,
            dob=dob,
            age=age,
            gender=gender,
            address_lane1=address_lane1,
            address_lane2=address_lane2,
            district=district,
            state=state,
            phone_no=phone_no,
            email=email,
            photo=filename,
            voter_id=voter_id,
            password=hashed_password
        )

        db.session.add(new_voter)
        db.session.commit()
        flash('Voter added successfully!', 'success')
        return redirect(url_for('voter_list'))

    return render_template('add_voter.html')
@app.route('/edit-voter/<int:id>', methods=['GET', 'POST'])
def edit_voter(id):
    voter = Voter.query.get_or_404(id)
    voter.password = ""  # Clear password field for security (optional display)

    if request.method == 'POST':
        voter.name = request.form['name']
        voter.email = request.form['email']
        voter.username = request.form['username']
        voter.age = request.form['age']
        voter.gender = request.form['gender']
        voter.address_lane1 = request.form['address_lane1']
        voter.address_lane2 = request.form['address_lane2']
        voter.district = request.form['district']
        voter.state = request.form['state']
        voter.phone_no = request.form['phone_no']

        # Handle photo upload
        if 'photo' in request.files:
            photo_file = request.files['photo']
            if photo_file and photo_file.filename != '':
                filename = secure_filename(photo_file.filename)
                photo_path = os.path.join('static/uploads', filename)  # Adjust folder path as needed
                photo_file.save(photo_path)
                voter.photo = photo_path  # Save path to DB

        # Update password if provided
        password = request.form['password']
        if password:
            voter.set_password(password)  # Assuming Voter model has set_password()

        db.session.commit()
        flash('Voter updated successfully!', 'success')
        return redirect(url_for('voter_list'))

    return render_template('edit_voter.html', voter=voter)

@app.route('/delete-voter/<int:id>', methods=['POST', 'GET'])
def delete_voter(id):
    voter = Voter.query.get_or_404(id)
    db.session.delete(voter)
    db.session.commit()
    flash('Voter deleted successfully!', 'success')
    return redirect(url_for('voter_list'))


@app.route('/voter-list')
def voter_list():
    voters = Voter.query.all()
    return render_template('voter_list.html', voters=voters)

@app.route('/add-candidate', methods=['GET', 'POST'])
def add_candidate():
    if request.method == 'POST':
        name = request.form['name']
        party_name = request.form['party_name']
        photo = request.files['party_symbol']
        candidate_id = f"CAND{len(Candidate.query.all()) + 1}"

        if photo and photo.filename != '':
            ext = photo.filename.rsplit('.', 1)[1].lower()
            filename = f"{candidate_id}.{ext}"
            upload_path = os.path.join('static', 'uploads')
            os.makedirs(upload_path, exist_ok=True)
            photo.save(os.path.join(upload_path, filename))

        new_candidate = Candidate(
            name=name,
            party_name=party_name,
            party_symbol=filename,
            candidate_id=candidate_id
        )

        db.session.add(new_candidate)
        db.session.commit()
        flash('Candidate added successfully!', 'success')
        return redirect(url_for('candidate_list'))

    return render_template('add_candidate.html')

@app.route('/candidate-list')
def candidate_list():
    candidates = Candidate.query.all()
    return render_template('candidate_list.html', candidates=candidates)

@app.route('/edit-candidate/<int:id>', methods=['GET', 'POST'])
def edit_candidate(id):
    candidate = Candidate.query.get_or_404(id)
    if request.method == 'POST':
        candidate.name = request.form['name']
        candidate.party = request.form['party']
        candidate.photo = request.files['photo']
        db.session.commit()
        flash('Candidate updated successfully!', 'success')
        return redirect(url_for('candidate_management'))
    return render_template('edit_candidate.html', candidate=candidate)
@app.route('/delete-candidate/<int:id>', methods=['POST', 'GET'])
def delete_candidate(id):
    candidate = Candidate.query.get_or_404(id)
    db.session.delete(candidate)
    db.session.commit()
    flash('Candidate deleted successfully!', 'success')
    return redirect(url_for('candidate_management'))

@app.route('/fix-election', methods=['GET', 'POST'])
def fix_election():
    if request.method == 'POST':
        start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
        candidates = request.form.getlist('candidates')

        # Reset votes and voter status
        Vote.query.delete()
        Voter.query.update({Voter.has_voted: False})

        new_election = Election(
            start_time=start_time,
            end_time=end_time,
            election_going=True
        )

        # Add candidates to the election
        for candidate_id in candidates:
            candidate = Candidate.query.get(candidate_id)
            new_election.candidates.append(candidate)

        db.session.add(new_election)
        db.session.commit()
        flash('Election fixed successfully!', 'success')

        return redirect(url_for('election_management'))

    candidates = Candidate.query.all()
    return render_template('fix_election.html', candidates=candidates)

@app.route('/force-stop')
def force_stop():
    election = Election.query.filter_by(election_going=True).order_by(Election.id.desc()).first()
    if election:
        election.election_going = False
        db.session.commit()
        flash('Election force stopped!', 'success')
    
    return redirect(url_for('election_management'))

@app.route('/create-dummy-admin')
def create_dummy_admin():
    # Check if admin already exists to avoid duplicates
    existing_admin = Admin.query.filter_by(username='admin').first()
    if existing_admin:
        flash('Admin already exists.', 'info')
        return redirect(url_for('admin_login'))

    # Create new admin
    new_admin = Admin(username='admin')
    new_admin.set_password('admin123')  # Set a hashed password

    db.session.add(new_admin)
    db.session.commit()

    flash('Dummy admin created successfully!', 'success')
    return redirect(url_for('admin_login'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
