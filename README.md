# Municipal Waste Management System

A comprehensive waste management system designed for Local Government Units (LGUs) to track waste collection across different barangays using QR code technology.

## Features

- **Municipality & Barangay Management**: Integration with Philippine Standard Geographic Code (PSGC) API for real-time barangay data
- **QR Code Generation & Scanning**: Generate unique QR codes for waste items and scan them for tracking
- **Collection Tracking**: Monitor waste collection status across different barangays
- **Collection Team Dashboard**: Interface for collection teams to manage pending collections
- **Analytics Dashboard**: View statistics and reports on waste collection performance
- **Real-time Status Updates**: Track waste items from registration to disposal

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (with SQLAlchemy ORM)
- **Frontend**: Bootstrap 5, HTML5, JavaScript
- **QR Code**: qrcode library
- **API Integration**: PSGC Cloud API for Philippine geographic data

## Installation

1. **Clone or download the project files**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**:
   ```bash
   python init_db.py
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Access the application**:
   Open your browser and go to `http://localhost:5000`

## Setup for Your Municipality

### 1. Sync Municipalities from API

1. Go to the **Municipalities** page in the navigation
2. Click **"Sync from API"** to fetch all municipalities and cities from the PSGC API
3. Find your municipality in the list

### 2. Sync Barangays for Your Municipality

1. In the Municipalities page, find your municipality
2. Click **"Sync Barangays"** to fetch all barangays for your municipality
3. Verify that all barangays are loaded correctly

### 3. Configure Collection Routes (Optional)

1. Go to **Collection Routes** to set up collection schedules
2. Assign specific days and times for each barangay

## Running the Application

### Start the Server
```bash
python app.py
```

### Access the System
- **Local Access**: `http://localhost:5000`
- **Network Access**: `http://192.168.1.128:5000` (replace with your device's IP address)

**Note**: The system runs on HTTP and is accessible from any device on the same network. Camera access may require permission from the browser.

## Usage

### For LGU Staff

1. **Register Waste Items**:
   - Go to "Register Waste Item"
   - Select municipality and barangay
   - Fill in waste item details
   - Generate QR code for tracking

2. **Monitor Collection Status**:
   - Use "Collection Status" to view progress by barangay
   - Check "Collection Team" for pending collections
   - View analytics in the Dashboard

### For Collection Teams

1. **View Pending Collections**:
   - Go to "Collection Team" dashboard
   - See all pending waste items by barangay
   - Mark items as collected when picked up

2. **Update Item Status**:
   - Scan QR codes or manually update status
   - Track items through the collection process

### For Citizens

1. **Register Waste for Collection**:
   - Use the "Register Waste Item" form
   - Select your barangay
   - Get a QR code for tracking

## API Integration

The system integrates with the **PSGC Cloud API** to fetch real-time data about:

- Municipalities and cities
- Barangays within each municipality
- Geographic codes and administrative divisions

### API Endpoints Used

- `GET /api/cities-municipalities` - Fetch all municipalities
- `GET /api/cities-municipalities/{code}/barangays` - Fetch barangays for a municipality

## Database Schema

### Key Tables

- **Municipality**: Stores municipality/city information
- **Barangay**: Stores barangay information linked to municipalities
- **WasteItem**: Stores waste item details with QR code data
- **WasteTracking**: Tracks status changes and location updates
- **CollectionRoute**: Defines collection schedules by barangay

## Customization

### Adding New Waste Types

Edit the waste type options in `templates/add_waste.html`:

```html
<option value="your_waste_type">Your Waste Type</option>
```

### Modifying Collection Statuses

Update the status options in `app.py` and related templates:

```python
status = db.Column(db.String(50), default='pending_collection')
```

### Styling

The system uses Bootstrap 5. Customize the appearance by modifying the CSS in `templates/base.html` or adding custom stylesheets.

## Troubleshooting

### Common Issues

1. **API Connection Issues**:
   - Check internet connection
   - Verify PSGC API is accessible
   - Check console for error messages

2. **Database Issues**:
   - Run `python init_db.py` to reinitialize
   - Check SQLite file permissions

3. **QR Code Issues**:
   - Ensure camera permissions are granted
   - Use modern browsers with camera support

### Support

For technical support or customization requests, please contact your system administrator.

## License

This project is designed for municipal use. Please ensure compliance with local data protection and privacy regulations.

## Version

Version 1.0 - Municipal Waste Management System with PSGC API Integration
