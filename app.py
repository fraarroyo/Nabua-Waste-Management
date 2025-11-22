from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session, abort
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

class Barangay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), nullable=False, unique=True)
    municipality = db.Column(db.String(100), nullable=False, default='Nabua')
    province = db.Column(db.String(100), nullable=False, default='Camarines Sur')
    region = db.Column(db.String(100), nullable=False, default='Region V (Bicol Region)')
    population = db.Column(db.Integer, nullable=True)
    area_km2 = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
        user = db.session.get(User, session['user_id'])
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
        user = db.session.get(User, session['user_id'])
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
        user = db.session.get(User, session['user_id'])
        if not user or not (user.is_barangay() or user.is_admin()):
            flash('Barangay access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
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
    client_confirmed = db.Column(db.Boolean, default=False, nullable=False)  # Client confirmation for collection
    client_confirmed_at = db.Column(db.DateTime, nullable=True)  # When client confirmed
    is_sorted = db.Column(db.Boolean, default=False, nullable=False)  # Whether waste is sorted
    sorted_at = db.Column(db.DateTime, nullable=True)  # When waste was marked as sorted
    sorted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Who marked it as sorted
    
    barangay = db.relationship('Barangay', backref=db.backref('waste_items', lazy=True))
    collection_route = db.relationship('CollectionRoute', backref=db.backref('waste_items', lazy=True))
    creator = db.relationship('User', foreign_keys=[created_by], backref=db.backref('created_waste_items', lazy=True))
    sorter = db.relationship('User', foreign_keys=[sorted_by], backref=db.backref('sorted_waste_items', lazy=True))

class WasteTracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    waste_item_id = db.Column(db.Integer, db.ForeignKey('waste_item.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    waste_item = db.relationship('WasteItem', backref=db.backref('tracking_records', lazy=True))

# API Functions
def sync_barangays():
    """Sync barangays for Nabua only"""
    print("Checking barangay data...")
    
    # Check if barangays already exist
    existing_count = Barangay.query.count()
    if existing_count > 0:
        print(f"Found {existing_count} existing barangays")
        return True
    
    print("No barangays found, initializing...")
    # Use the local script to add Nabua barangays
    from add_nabua_barangays import add_nabua_barangays
    add_nabua_barangays()
    
    # Verify barangays were added
    final_count = Barangay.query.count()
    print(f"Barangay initialization complete: {final_count} barangays loaded")
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

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = get_current_user()
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login'))
    
    # Get user statistics
    total_waste_items = WasteItem.query.filter_by(created_by=user.id).count()
    pending_items = WasteItem.query.filter_by(created_by=user.id, status='pending_collection').count()
    collected_items = WasteItem.query.filter_by(created_by=user.id, status='collected').count()
    
    return render_template('profile.html', 
                         user=user,
                         total_waste_items=total_waste_items,
                         pending_items=pending_items,
                         collected_items=collected_items)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page - allows users to update their own profile"""
    user = get_current_user()
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email', '')
        full_name = request.form.get('full_name', '')
        phone = request.form.get('phone', '')
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate required fields
        if not email or not full_name:
            flash('Please fill in all required fields.', 'error')
            return render_template('settings.html', user=user)
        
        # Check if email is already taken by another user
        existing_email = User.query.filter(User.email == email, User.id != user.id).first()
        if existing_email:
            flash('Email already exists!', 'error')
            return render_template('settings.html', user=user)
        
        try:
            # Update user information
            user.email = email
            user.full_name = full_name
            user.phone = phone if phone else None
            
            # Update password if provided
            if new_password:
                if not current_password:
                    flash('Please enter your current password to change it.', 'error')
                    return render_template('settings.html', user=user)
                
                if not user.check_password(current_password):
                    flash('Current password is incorrect.', 'error')
                    return render_template('settings.html', user=user)
                
                if new_password != confirm_password:
                    flash('New passwords do not match.', 'error')
                    return render_template('settings.html', user=user)
                
                if len(new_password) < 6:
                    flash('New password must be at least 6 characters long.', 'error')
                    return render_template('settings.html', user=user)
                
                user.set_password(new_password)
            
            db.session.commit()
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('settings'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating settings: {str(e)}', 'error')
    
    return render_template('settings.html', user=user)

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
            barangays = Barangay.query.filter_by(is_active=True).all()
            return render_template('add_waste.html', barangays=barangays)
        
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
        barangay = db.session.get(Barangay, barangay_id)
        qr_data = {
            'item_id': item_id,
            'item_name': item_name,
            'waste_type': waste_type,
            'barangay': barangay.name if barangay else 'N/A',
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
    
    barangays = Barangay.query.filter_by(is_active=True).all()
    return render_template('add_waste.html', barangays=barangays)

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
    
    # Get collected items waiting for client confirmation
    awaiting_confirmation = WasteItem.query.join(Barangay).filter(
        WasteItem.status == 'collected',
        WasteItem.client_confirmed == False
    ).order_by(WasteItem.updated_at.desc()).all()
    
    return render_template('collection_team.html', 
                         pending_collections=pending_collections,
                         awaiting_confirmation=awaiting_confirmation)

@app.route('/mark_collected/<item_id>', methods=['POST'])
def mark_collected(item_id):
    waste_item = WasteItem.query.filter_by(item_id=item_id).first_or_404()
    
    # Check if waste is sorted before allowing collection
    if not waste_item.is_sorted:
        flash('Cannot collect waste that is not sorted. Please mark the waste as sorted first.', 'error')
        return redirect(url_for('collection_team'))
    
    # Only allow collection if status is pending_collection
    if waste_item.status != 'pending_collection':
        flash('This waste item cannot be collected in its current status.', 'warning')
        return redirect(url_for('collection_team'))
    
    waste_item.status = 'collected'
    waste_item.client_confirmed = False  # Require client confirmation
    waste_item.updated_at = datetime.utcnow()
    
    # Add tracking record
    tracking = WasteTracking(
        waste_item_id=waste_item.id,
        status='collected',
        location=waste_item.address,
        notes=f'Collected by collection team at {datetime.now().strftime("%Y-%m-%d %H:%M")}. Waiting for client confirmation.'
    )
    
    db.session.add(tracking)
    db.session.commit()
    
    flash('Waste item marked as collected! Waiting for client confirmation.', 'success')
    return redirect(url_for('collection_team'))

@app.route('/mark_sorted/<item_id>', methods=['POST'])
@login_required
def mark_sorted(item_id):
    """Mark waste as sorted (can be done by creator, collector, or admin)"""
    waste_item = WasteItem.query.filter_by(item_id=item_id).first_or_404()
    current_user = get_current_user()
    
    # Only allow marking as sorted if status is pending_collection
    if waste_item.status != 'pending_collection':
        flash('Waste can only be marked as sorted when it is pending collection.', 'warning')
        return redirect(url_for('view_item', item_id=item_id))
    
    if waste_item.is_sorted:
        flash('This waste item is already marked as sorted.', 'info')
        return redirect(url_for('view_item', item_id=item_id))
    
    # Mark as sorted
    waste_item.is_sorted = True
    waste_item.sorted_at = datetime.utcnow()
    waste_item.sorted_by = current_user.id
    waste_item.updated_at = datetime.utcnow()
    
    # Add tracking record
    tracking = WasteTracking(
        waste_item_id=waste_item.id,
        status='pending_collection',
        location=waste_item.address,
        notes=f'Waste marked as sorted by {current_user.full_name} at {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    )
    
    db.session.add(tracking)
    db.session.commit()
    
    flash('Waste marked as sorted successfully! It is now ready for collection.', 'success')
    return redirect(url_for('view_item', item_id=item_id))

@app.route('/mark_unsorted/<item_id>', methods=['POST'])
@login_required
def mark_unsorted(item_id):
    """Mark waste as unsorted and uncollected"""
    waste_item = WasteItem.query.filter_by(item_id=item_id).first_or_404()
    current_user = get_current_user()
    
    # Only allow if user is creator, collector, or admin
    if waste_item.created_by != current_user.id and not current_user.is_collector() and not current_user.is_admin():
        flash('You do not have permission to mark this waste as unsorted.', 'error')
        return redirect(url_for('view_item', item_id=item_id))
    
    # Mark as unsorted and reset to pending_collection if it was collected
    waste_item.is_sorted = False
    waste_item.sorted_at = None
    waste_item.sorted_by = None
    
    # If waste was collected but not sorted, mark as uncollected
    if waste_item.status == 'collected':
        waste_item.status = 'pending_collection'
        waste_item.client_confirmed = False
        waste_item.client_confirmed_at = None
        
        # Add tracking record
        tracking = WasteTracking(
            waste_item_id=waste_item.id,
            status='pending_collection',
            location=waste_item.address,
            notes=f'Waste marked as unsorted and uncollected by {current_user.full_name} at {datetime.now().strftime("%Y-%m-%d %H:%M")}. Waste must be sorted before collection.'
        )
    else:
        # Add tracking record
        tracking = WasteTracking(
            waste_item_id=waste_item.id,
            status=waste_item.status,
            location=waste_item.address,
            notes=f'Waste marked as unsorted by {current_user.full_name} at {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        )
    
    waste_item.updated_at = datetime.utcnow()
    db.session.add(tracking)
    db.session.commit()
    
    flash('Waste marked as unsorted. It must be sorted before collection.', 'warning')
    return redirect(url_for('view_item', item_id=item_id))

@app.route('/confirm_collection/<item_id>', methods=['POST'])
@login_required
def confirm_collection(item_id):
    """Allow client (creator) to confirm that waste was collected"""
    waste_item = WasteItem.query.filter_by(item_id=item_id).first_or_404()
    current_user = get_current_user()
    
    # Check if user is the creator or admin
    if waste_item.status != 'collected':
        flash('This item has not been marked as collected yet.', 'warning')
        return redirect(url_for('view_item', item_id=item_id))
    
    if waste_item.client_confirmed:
        flash('This item has already been confirmed.', 'info')
        return redirect(url_for('view_item', item_id=item_id))
    
    # Only allow the creator or admin to confirm
    if waste_item.created_by != current_user.id and not current_user.is_admin():
        flash('You do not have permission to confirm this collection.', 'error')
        return redirect(url_for('view_item', item_id=item_id))
    
    # Confirm the collection
    waste_item.client_confirmed = True
    waste_item.client_confirmed_at = datetime.utcnow()
    waste_item.updated_at = datetime.utcnow()
    
    # Add tracking record
    tracking = WasteTracking(
        waste_item_id=waste_item.id,
        status='collected',
        location=waste_item.address,
        notes=f'Collection confirmed by client at {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    )
    
    db.session.add(tracking)
    db.session.commit()
    
    flash('Collection confirmed successfully! Thank you for confirming.', 'success')
    return redirect(url_for('view_item', item_id=item_id))

@app.route('/api/barangays')
def api_barangays():
    """Get all barangays"""
    barangays = Barangay.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': brgy.id,
        'name': brgy.name,
        'code': brgy.code,
        'municipality': brgy.municipality,
        'province': brgy.province,
        'region': brgy.region,
        'population': brgy.population,
        'area_km2': brgy.area_km2
    } for brgy in barangays])

@app.route('/api/barangays/sync', methods=['POST'])
def sync_barangays_api():
    """Sync barangays for Nabua only"""
    try:
        success = sync_barangays()
        if success:
            return jsonify({'success': True, 'message': 'Nabua barangays synced successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to sync Nabua barangays'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/barangays/force-sync', methods=['POST'])
def force_sync_barangays_api():
    """Force sync barangays (for deployment issues)"""
    try:
        # Clear existing barangays and re-sync
        Barangay.query.delete()
        db.session.commit()
        
        from add_nabua_barangays import add_nabua_barangays
        add_nabua_barangays()
        
        count = Barangay.query.count()
        return jsonify({'success': True, 'message': f'Force sync completed: {count} barangays loaded'})
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


@app.route('/api/items')
def api_items():
    items = WasteItem.query.join(Barangay).all()
    return jsonify([{
        'id': item.id,
        'item_id': item.item_id,
        'item_name': item.item_name,
        'waste_type': item.waste_type,
        'status': item.status,
        'barangay': item.barangay.name,
        'municipality': item.barangay.municipality,
        'address': item.address,
        'created_at': item.created_at.isoformat()
    } for item in items])

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a user account"""
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    
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
    current_user = db.session.get(User, session.get('user_id')) if session.get('user_id') else None
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
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    
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

def backup_user_data():
    """Create a backup of user data for safety"""
    try:
        users = User.query.all()
        backup_data = []
        for user in users:
            backup_data.append({
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'phone': user.phone,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        
        # Save backup to a JSON file
        import json
        with open('user_backup.json', 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        print(f"User data backed up to user_backup.json ({len(backup_data)} users)")
        return True
    except Exception as e:
        print(f"Failed to backup user data: {e}")
        return False

def check_database_health():
    """Check database health and ensure data persistence"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        print("Database connection is healthy")
        
        # Check if tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        required_tables = ['user', 'barangay', 'waste_item', 'waste_tracking', 'collection_route']
        
        missing_tables = [table for table in required_tables if table not in tables]
        if missing_tables:
            print(f"Missing tables: {missing_tables}")
            return False
        else:
            print("All required tables exist")
            return True
            
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False

def initialize_database():
    """Initialize database tables only if they don't exist - NEVER drop existing tables"""
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        required_tables = ['user', 'barangay', 'waste_item', 'waste_tracking', 'collection_route']
        
        # Check if database file exists
        db_file = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        db_exists = os.path.exists(db_file) if db_file else False
        
        # Only create tables if they don't exist
        if not existing_tables or not all(table in existing_tables for table in required_tables):
            print("Creating missing database tables...")
            db.create_all()
            print("Database tables created successfully")
            return True
        else:
            print("Database tables already exist - preserving all data")
            return True
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        # If there's an error, try to create tables anyway (first run)
        try:
            db.create_all()
            print("Database tables created after error recovery")
            return True
        except Exception as e2:
            print(f"Failed to create database tables: {e2}")
            return False

def create_default_users():
    """Create only the main admin account and preserve existing users"""
    # Count existing users
    total_users = User.query.count()
    print(f"📊 Found {total_users} existing users in the database")
    
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
        print("Admin account created successfully!")
    else:
        print("Admin account already exists")
    
    # Commit changes
    db.session.commit()
    
    # Count users after creation
    final_user_count = User.query.count()
    print(f"📊 Total users in database: {final_user_count}")
    
    # List all users for verification
    all_users = User.query.all()
    print("\n👥 Current users in the system:")
    for user in all_users:
        print(f"  - {user.username} ({user.role}) - {user.full_name}")
    
    print("\n" + "="*50)
    print("🎉 SYSTEM INITIALIZATION COMPLETE")
    print("="*50)
    print("Admin Account:")
    print("  Username: admin        | Password: admin123")
    print("="*50)
    print("All existing users have been preserved!")
    print("You can now log in to the system!")
    print("="*50)

if __name__ == '__main__':
    with app.app_context():
        print("Starting Nabua Waste Management System...")
        print("="*50)
        
        # Initialize database - only creates tables if they don't exist
        # NEVER drops existing tables to preserve data
        initialize_database()
        
        # Check database health (read-only check)
        check_database_health()
        
        # Create backup of existing users (for safety)
        backup_user_data()
        
        # Initialize barangays if they don't exist
        sync_barangays()
        
        # Create default users on first run (only if admin doesn't exist)
        create_default_users()
    
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Get debug mode from environment variable
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
