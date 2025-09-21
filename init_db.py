from app import app, db, Municipality, Barangay, CollectionRoute
from datetime import datetime

def init_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if municipalities already exist
        if Municipality.query.count() == 0:
            # Sample municipalities
            sample_municipalities = [
                {'name': 'Sample Municipality', 'code': 'SMPL', 'province': 'Sample Province', 'region': 'Sample Region'},
            ]
            
            # Add municipalities
            for mun_data in sample_municipalities:
                municipality = Municipality(**mun_data)
                db.session.add(municipality)
            
            db.session.commit()
            print("Sample municipality added successfully!")
            
            # Get the municipality
            municipality = Municipality.query.first()
            
            # Sample barangays for the municipality
            sample_barangays = [
                {'name': 'Barangay Poblacion', 'code': 'POB', 'municipality_id': municipality.id, 'population': 5000, 'area_km2': 2.5},
                {'name': 'Barangay San Jose', 'code': 'SJ', 'municipality_id': municipality.id, 'population': 3500, 'area_km2': 1.8},
                {'name': 'Barangay Santa Maria', 'code': 'SM', 'municipality_id': municipality.id, 'population': 4200, 'area_km2': 2.1},
                {'name': 'Barangay San Isidro', 'code': 'SI', 'municipality_id': municipality.id, 'population': 3800, 'area_km2': 1.9},
                {'name': 'Barangay San Antonio', 'code': 'SA', 'municipality_id': municipality.id, 'population': 3100, 'area_km2': 1.6},
                {'name': 'Barangay San Miguel', 'code': 'SMG', 'municipality_id': municipality.id, 'population': 2800, 'area_km2': 1.4},
                {'name': 'Barangay San Pedro', 'code': 'SP', 'municipality_id': municipality.id, 'population': 2600, 'area_km2': 1.3},
                {'name': 'Barangay San Rafael', 'code': 'SR', 'municipality_id': municipality.id, 'population': 2400, 'area_km2': 1.2},
            ]
            
            # Add barangays
            for barangay_data in sample_barangays:
                barangay = Barangay(**barangay_data)
                db.session.add(barangay)
            
            db.session.commit()
            print("Sample barangays added successfully!")
            
            # Add collection routes
            barangays = Barangay.query.all()
            collection_routes = [
                {'route_name': 'Route 1 - Poblacion', 'barangay_id': barangays[0].id, 'collection_day': 'Monday', 'collection_time': '08:00'},
                {'route_name': 'Route 2 - San Jose', 'barangay_id': barangays[1].id, 'collection_day': 'Tuesday', 'collection_time': '08:00'},
                {'route_name': 'Route 3 - Santa Maria', 'barangay_id': barangays[2].id, 'collection_day': 'Wednesday', 'collection_time': '08:00'},
                {'route_name': 'Route 4 - San Isidro', 'barangay_id': barangays[3].id, 'collection_day': 'Thursday', 'collection_time': '08:00'},
                {'route_name': 'Route 5 - San Antonio', 'barangay_id': barangays[4].id, 'collection_day': 'Friday', 'collection_time': '08:00'},
                {'route_name': 'Route 6 - San Miguel', 'barangay_id': barangays[5].id, 'collection_day': 'Monday', 'collection_time': '14:00'},
                {'route_name': 'Route 7 - San Pedro', 'barangay_id': barangays[6].id, 'collection_day': 'Tuesday', 'collection_time': '14:00'},
                {'route_name': 'Route 8 - San Rafael', 'barangay_id': barangays[7].id, 'collection_day': 'Wednesday', 'collection_time': '14:00'},
            ]
            
            for route_data in collection_routes:
                route = CollectionRoute(**route_data)
                db.session.add(route)
            
            db.session.commit()
            print("Collection routes added successfully!")
        else:
            print("Database already initialized!")

if __name__ == '__main__':
    init_database()
