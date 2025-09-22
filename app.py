from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import qrcode
from io import BytesIO
import base64
import os
from datetime import datetime
import json
import requests

# QR scanning is handled entirely by JavaScript (jsQR library)
QR_SCANNING_AVAILABLE = True

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///waste_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='barangay')  # admin, collector, barangay
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_collector(self):
        return self.role == 'collector'
    
    def is_barangay(self):
        return self.role == 'barangay'

class Municipality(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), nullable=False, unique=True)
    province = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Barangay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    municipality_id = db.Column(db.Integer, db.ForeignKey('municipality.id'), nullable=False)
    population = db.Column(db.Integer, nullable=True)
    area_km2 = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    municipality = db.relationship('Municipality', backref=db.backref('barangays', lazy=True))

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def collector_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not (user.is_collector() or user.is_admin()):
            flash('Collection team access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def barangay_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not (user.is_barangay() or user.is_admin()):
            flash('Barangay access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

class CollectionRoute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route_name = db.Column(db.String(100), nullable=False)
    barangay_id = db.Column(db.Integer, db.ForeignKey('barangay.id'), nullable=False)
    collection_day = db.Column(db.String(20), nullable=False)  # Monday, Tuesday, etc.
    collection_time = db.Column(db.String(10), nullable=False)  # 08:00, 14:00, etc.
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    barangay = db.relationship('Barangay', backref=db.backref('collection_routes', lazy=True))

class WasteItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.String(50), unique=True, nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    waste_type = db.Column(db.String(50), nullable=False)  # recyclable, hazardous, organic, etc.
    weight = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending_collection')  # pending_collection, collected, in_transit, processed, disposed
    barangay_id = db.Column(db.Integer, db.ForeignKey('barangay.id'), nullable=False)
    collection_route_id = db.Column(db.Integer, db.ForeignKey('collection_route.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Track who created the item
    address = db.Column(db.String(200), nullable=True)
    contact_person = db.Column(db.String(100), nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    qr_code_data = db.Column(db.Text, nullable=True)
    
    barangay = db.relationship('Barangay', backref=db.backref('waste_items', lazy=True))
    collection_route = db.relationship('CollectionRoute', backref=db.backref('waste_items', lazy=True))
    creator = db.relationship('User', backref=db.backref('created_waste_items', lazy=True))

class WasteTracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    waste_item_id = db.Column(db.Integer, db.ForeignKey('waste_item.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    waste_item = db.relationship('WasteItem', backref=db.backref('tracking_records', lazy=True))

# API Functions
def fetch_municipalities_from_api():
    """Fetch municipalities from PSGC API"""
    try:
        # Using PSGC Cloud API
        response = requests.get('https://psgc.cloud/api/cities-municipalities', timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        print(f"Error fetching municipalities: {e}")
        return []

def fetch_barangays_from_api(municipality_code):
    """Fetch barangays for a specific municipality from PSGC API"""
    try:
        response = requests.get(f'https://psgc.cloud/api/cities-municipalities/{municipality_code}/barangays', timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        print(f"Error fetching barangays: {e}")
        return []

def sync_municipalities():
    """Sync only Nabua municipality to database"""
    # Only sync Nabua municipality - no external API calls
    nabua = Municipality.query.filter_by(name='Nabua').first()
    if not nabua:
        nabua = Municipality(
            name='Nabua',
            code='NBN',
            province='Camarines Sur',
            region='Region V (Bicol Region)',
            is_active=True
        )
        db.session.add(nabua)
        db.session.commit()
        print("Nabua municipality created!")
    else:
        print("Nabua municipality already exists!")
    
    return True

def sync_barangays(municipality_id):
    """Sync barangays for Nabua municipality only"""
    municipality = Municipality.query.get(municipality_id)
    if not municipality or municipality.name != 'Nabua':
        return False
    
    # Only sync if it's Nabua municipality
    if Barangay.query.filter_by(municipality_id=municipality_id).count() > 0:
        print("Barangays for Nabua already exist!")
        return True
    
    # Use the local script to add Nabua barangays
    from add_nabua_barangays import add_nabua_barangays
    add_nabua_barangays()
    return True

# Routes
# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, is_active=True).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    # Get statistics for dashboard
    total_waste_items = WasteItem.query.count()
    pending_collection = WasteItem.query.filter_by(status='pending_collection').count()
    collected_today = WasteItem.query.filter(
        WasteItem.status == 'collected',
        db.func.date(WasteItem.updated_at) == db.func.date('now')
    ).count()
    
    # Get recent waste items
    recent_items = WasteItem.query.join(Barangay).order_by(WasteItem.created_at.desc()).limit(10).all()
    
    # Get barangay statistics
    barangay_stats = db.session.query(
        Barangay.name,
        db.func.count(WasteItem.id).label('total_items'),
        db.func.count(db.case((WasteItem.status == 'pending_collection', 1), else_=None)).label('pending_items')
    ).outerjoin(WasteItem).group_by(Barangay.id, Barangay.name).all()
    
    return render_template('index.html', 
                         waste_items=recent_items,
                         total_waste_items=total_waste_items,
                         pending_collection=pending_collection,
                         collected_today=collected_today,
                         barangay_stats=barangay_stats)

@app.route('/add_waste', methods=['GET', 'POST'])
@barangay_required
def add_waste():
    if request.method == 'POST':
        waste_type = request.form.get('waste_type', '')
        weight = float(request.form['weight']) if request.form.get('weight') else None
        description = request.form.get('description', '')
        barangay_id = int(request.form['barangay_id'])
        address = request.form.get('address', '')
        contact_person = request.form.get('contact_person', '')
        contact_number = request.form.get('contact_number', '')
        
        # Validate required fields
        if not waste_type or not barangay_id:
            flash('Please fill in all required fields.', 'error')
            municipalities = Municipality.query.filter_by(name='Nabua', is_active=True).all()
            return render_template('add_waste.html', municipalities=municipalities)
        
        # Generate unique item ID
        item_id = f"WM{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Get current time for timestamps
        current_time = datetime.utcnow()
        
        # Generate item name based on waste type
        waste_type_names = {
            'recyclable': 'Recyclable Waste',
            'hazardous': 'Hazardous Waste',
            'organic': 'Organic Waste',
            'electronic': 'Electronic Waste',
            'medical': 'Medical Waste',
            'other': 'Other Waste'
        }
        item_name = waste_type_names.get(waste_type, 'Waste Item')
        
        # Create waste item
        waste_item = WasteItem(
            item_id=item_id,
            item_name=item_name,
            waste_type=waste_type,
            weight=weight,
            description=description,
            barangay_id=barangay_id,
            created_by=session.get('user_id'),  # Set the creator
            address=address,
            contact_person=contact_person,
            contact_number=contact_number,
            status='pending_collection',
            created_at=current_time,
            updated_at=current_time
        )
        
        # Generate QR code data
        qr_data = {
            'item_id': item_id,
            'item_name': item_name,
            'waste_type': waste_type,
            'barangay': Barangay.query.get(barangay_id).name,
            'created_at': current_time.isoformat()
        }
        waste_item.qr_code_data = json.dumps(qr_data)
        
        db.session.add(waste_item)
        db.session.commit()
        
        # Add initial tracking record
        tracking = WasteTracking(
            waste_item_id=waste_item.id,
            status='pending_collection',
            location=address,
            notes='Waste item registered for collection'
        )
        db.session.add(tracking)
        db.session.commit()
        
        flash('Waste registered for collection successfully! Collection team will be notified.', 'success')
        return redirect(url_for('view_item', item_id=waste_item.item_id))
    
    municipalities = Municipality.query.filter_by(name='Nabua', is_active=True).all()
    return render_template('add_waste.html', municipalities=municipalities)

@app.route('/item/<item_id>')
def view_item(item_id):
    waste_item = WasteItem.query.filter_by(item_id=item_id).first_or_404()
    tracking_records = WasteTracking.query.filter_by(waste_item_id=waste_item.id).order_by(WasteTracking.timestamp.desc()).all()
    return render_template('view_item.html', waste_item=waste_item, tracking_records=tracking_records)

@app.route('/generate_qr/<item_id>')
def generate_qr(item_id):
    waste_item = WasteItem.query.filter_by(item_id=item_id).first_or_404()
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(waste_item.qr_code_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for web display
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return render_template('qr_code.html', waste_item=waste_item, qr_code=img_str)

@app.route('/scan_qr', methods=['GET', 'POST'])
@collector_required
def scan_qr():
    if request.method == 'POST':
        # Handle QR code scanning (this would typically be done via JavaScript with camera)
        scanned_data = request.json.get('qr_data')
        if scanned_data:
            try:
                qr_data = json.loads(scanned_data)
                item_id = qr_data.get('item_id')
                waste_item = WasteItem.query.filter_by(item_id=item_id).first()
                if waste_item:
                    return jsonify({
                        'success': True,
                        'item': {
                            'item_id': waste_item.item_id,
                            'item_name': waste_item.item_name,
                            'waste_type': waste_item.waste_type,
                            'status': waste_item.status,
                            'address': waste_item.address,
                            'barangay': waste_item.barangay.name if waste_item.barangay else 'N/A'
                        }
                    })
                else:
                    return jsonify({'success': False, 'error': 'Item not found'})
            except json.JSONDecodeError:
                return jsonify({'success': False, 'error': 'Invalid QR code data'})
    
    return render_template('scan_qr.html', qr_scanning_available=QR_SCANNING_AVAILABLE)

@app.route('/update_status/<item_id>', methods=['POST'])
def update_status(item_id):
    waste_item = WasteItem.query.filter_by(item_id=item_id).first_or_404()
    new_status = request.form['status']
    location = request.form.get('location', waste_item.address)
    notes = request.form.get('notes', '')
    
    # Update waste item status
    waste_item.status = new_status
    waste_item.updated_at = datetime.utcnow()
    
    # Add tracking record
    tracking = WasteTracking(
        waste_item_id=waste_item.id,
        status=new_status,
        location=location,
        notes=notes
    )
    
    db.session.add(tracking)
    db.session.commit()
    
    flash('Status updated successfully!', 'success')
    return redirect(url_for('view_item', item_id=item_id))

@app.route('/barangays')
def barangays():
    barangay_list = Barangay.query.filter_by(is_active=True).all()
    return render_template('barangays.html', barangays=barangay_list)

@app.route('/collection_routes')
def collection_routes():
    routes = CollectionRoute.query.join(Barangay).filter(CollectionRoute.is_active == True).all()
    return render_template('collection_routes.html', routes=routes)

@app.route('/collection_status')
def collection_status():
    # Get collection status by barangay
    barangay_collections = db.session.query(
        Barangay.name,
        db.func.count(WasteItem.id).label('total_items'),
        db.func.count(db.case((WasteItem.status == 'pending_collection', 1), else_=None)).label('pending'),
        db.func.count(db.case((WasteItem.status == 'collected', 1), else_=None)).label('collected'),
        db.func.count(db.case((WasteItem.status == 'processed', 1), else_=None)).label('processed')
    ).outerjoin(WasteItem).group_by(Barangay.id, Barangay.name).all()
    
    return render_template('collection_status.html', barangay_collections=barangay_collections)

@app.route('/dashboard')
@login_required
def dashboard():
    # Get comprehensive statistics
    total_waste_items = WasteItem.query.count()
    pending_collection = WasteItem.query.filter_by(status='pending_collection').count()
    collected = WasteItem.query.filter_by(status='collected').count()
    in_transit = WasteItem.query.filter_by(status='in_transit').count()
    processed = WasteItem.query.filter_by(status='processed').count()
    disposed = WasteItem.query.filter_by(status='disposed').count()
    
    # Get waste type statistics
    waste_type_stats = db.session.query(
        WasteItem.waste_type,
        db.func.count(WasteItem.id).label('count')
    ).group_by(WasteItem.waste_type).all()
    
    # Get barangay statistics
    barangay_stats = db.session.query(
        Barangay.name,
        db.func.count(WasteItem.id).label('total_items'),
        db.func.count(db.case((WasteItem.status == 'pending_collection', 1), else_=None)).label('pending_items')
    ).outerjoin(WasteItem).group_by(Barangay.id, Barangay.name).order_by(db.func.count(WasteItem.id).desc()).all()
    
    # Get recent waste items
    recent_items = WasteItem.query.order_by(WasteItem.created_at.desc()).limit(10).all()
    
    # Get collection team statistics
    total_routes = CollectionRoute.query.count()
    active_routes = CollectionRoute.query.filter_by(is_active=True).count() if hasattr(CollectionRoute, 'is_active') else total_routes
    
    return render_template('dashboard.html',
                         total_waste_items=total_waste_items,
                         pending_collection=pending_collection,
                         collected=collected,
                         in_transit=in_transit,
                         processed=processed,
                         disposed=disposed,
                         waste_type_stats=waste_type_stats,
                         barangay_stats=barangay_stats,
                         recent_items=recent_items,
                         total_routes=total_routes,
                         active_routes=active_routes)

@app.route('/collection_team')
@collector_required
def collection_team():
    # Get pending collections by barangay for collection team
    pending_collections = WasteItem.query.join(Barangay).filter(
        WasteItem.status == 'pending_collection'
    ).order_by(Barangay.name, WasteItem.created_at).all()
    
    return render_template('collection_team.html', pending_collections=pending_collections)

@app.route('/mark_collected/<item_id>', methods=['POST'])
def mark_collected(item_id):
    waste_item = WasteItem.query.filter_by(item_id=item_id).first_or_404()
    waste_item.status = 'collected'
    waste_item.updated_at = datetime.utcnow()
    
    # Add tracking record
    tracking = WasteTracking(
        waste_item_id=waste_item.id,
        status='collected',
        location=waste_item.address,
        notes=f'Collected by collection team at {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    )
    
    db.session.add(tracking)
    db.session.commit()
    
    flash('Waste item marked as collected!', 'success')
    return redirect(url_for('collection_team'))

@app.route('/api/municipalities')
def api_municipalities():
    """Get only Nabua municipality"""
    municipalities = Municipality.query.filter_by(name='Nabua', is_active=True).all()
    return jsonify([{
        'id': mun.id,
        'name': mun.name,
        'code': mun.code,
        'province': mun.province,
        'region': mun.region
    } for mun in municipalities])

@app.route('/api/municipalities/sync', methods=['POST'])
def sync_municipalities_api():
    """Sync only Nabua municipality"""
    try:
        success = sync_municipalities()
        if success:
            return jsonify({'success': True, 'message': 'Nabua municipality synced successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to sync Nabua municipality'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/municipalities/<int:municipality_id>/barangays')
def api_barangays(municipality_id):
    """Get barangays for a specific municipality"""
    barangays = Barangay.query.filter_by(municipality_id=municipality_id, is_active=True).all()
    return jsonify([{
        'id': brgy.id,
        'name': brgy.name,
        'code': brgy.code,
        'population': brgy.population,
        'area_km2': brgy.area_km2
    } for brgy in barangays])

@app.route('/api/municipalities/<int:municipality_id>/barangays/sync', methods=['POST'])
def sync_barangays_api(municipality_id):
    """Sync barangays for Nabua municipality only"""
    try:
        municipality = Municipality.query.get(municipality_id)
        if not municipality or municipality.name != 'Nabua':
            return jsonify({'success': False, 'message': 'Only Nabua municipality is supported'})
        
        success = sync_barangays(municipality_id)
        if success:
            return jsonify({'success': True, 'message': 'Nabua barangays synced successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to sync Nabua barangays'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/users')
@admin_required
def users():
    """User management page"""
    users = User.query.filter_by(is_active=True).all()
    return render_template('users.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
@admin_required
def add_user():
    """Add new user (admin only)"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '')
        phone = request.form.get('phone', '')
        role = request.form.get('role', '')
        
        # Validate required fields
        if not username or not email or not password or not full_name or not role:
            flash('Please fill in all required fields.', 'error')
            return render_template('add_user.html')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('add_user.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('add_user.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return render_template('add_user.html')
        
        # Create user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            role=role
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {username} created successfully!', 'success')
        return redirect(url_for('users'))
    
    return render_template('add_user.html')

@app.route('/municipalities')
@admin_required
def municipalities():
    """Municipality management page"""
    municipalities = Municipality.query.filter_by(is_active=True).all()
    return render_template('municipalities.html', municipalities=municipalities)

@app.route('/api/items')
def api_items():
    items = WasteItem.query.join(Barangay).join(Municipality).all()
    return jsonify([{
        'id': item.id,
        'item_id': item.item_id,
        'item_name': item.item_name,
        'waste_type': item.waste_type,
        'status': item.status,
        'barangay': item.barangay.name,
        'municipality': item.barangay.municipality.name,
        'address': item.address,
        'created_at': item.created_at.isoformat()
    } for item in items])

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a user account"""
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting the current user
    if user.id == session.get('user_id'):
        flash('You cannot delete your own account!', 'error')
        return redirect(url_for('users'))
    
    # Prevent deleting the main admin account
    if user.username == 'admin':
        flash('Cannot delete the main admin account!', 'error')
        return redirect(url_for('users'))
    
    try:
        # Delete associated waste items created by this user
        waste_items = WasteItem.query.filter_by(created_by=user.id).all()
        for item in waste_items:
            # Delete associated tracking records
            WasteTracking.query.filter_by(waste_item_id=item.id).delete()
            db.session.delete(item)
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User "{user.username}" has been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('users'))

@app.route('/delete_waste_item/<item_id>', methods=['POST'])
@login_required
def delete_waste_item(item_id):
    """Delete a waste item"""
    item = WasteItem.query.filter_by(item_id=item_id).first_or_404()
    
    # Only allow admin or the creator to delete
    current_user = User.query.get(session.get('user_id'))
    if current_user.role != 'admin' and item.created_by != current_user.id:
        flash('You do not have permission to delete this item!', 'error')
        return redirect(url_for('index'))
    
    try:
        # Delete associated tracking records
        WasteTracking.query.filter_by(waste_item_id=item.id).delete()
        
        # Delete the waste item
        db.session.delete(item)
        db.session.commit()
        
        flash(f'Waste item "{item.item_name}" has been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting waste item: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit user account"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username', '')
        email = request.form.get('email', '')
        full_name = request.form.get('full_name', '')
        phone = request.form.get('phone', '')
        role = request.form.get('role', '')
        password = request.form.get('password', '')  # Optional password change
        
        # Validate required fields
        if not username or not email or not full_name or not role:
            flash('Please fill in all required fields.', 'error')
            return render_template('edit_user.html', user=user)
        
        # Check if username is already taken by another user
        existing_user = User.query.filter(User.username == username, User.id != user_id).first()
        if existing_user:
            flash('Username already exists!', 'error')
            return render_template('edit_user.html', user=user)
        
        # Check if email is already taken by another user
        existing_email = User.query.filter(User.email == email, User.id != user_id).first()
        if existing_email:
            flash('Email already exists!', 'error')
            return render_template('edit_user.html', user=user)
        
        try:
            # Update user information
            user.username = username
            user.email = email
            user.full_name = full_name
            user.phone = phone
            user.role = role
            
            # Update password if provided
            if password:
                user.set_password(password)
            
            db.session.commit()
            flash(f'User "{user.username}" updated successfully!', 'success')
            return redirect(url_for('users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
    
    return render_template('edit_user.html', user=user)

def create_default_users():
    """Create only the main admin account"""
    # Check if admin user already exists
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin = User(
            username='admin',
            email='admin@nabua.gov.ph',
            full_name='System Administrator',
            phone='+63-999-000-0001',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("✅ Admin account created successfully!")
    else:
        print("ℹ️  Admin account already exists")
    
    # Commit changes
    db.session.commit()
    
    print("\n" + "="*50)
    print("🎉 ADMIN ACCOUNT CREATED")
    print("="*50)
    print("Admin Account:")
    print("  Username: admin        | Password: admin123")
    print("="*50)
    print("You can now log in to the system!")
    print("="*50)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default users on first run
        create_default_users()
    
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Get debug mode from environment variable
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
