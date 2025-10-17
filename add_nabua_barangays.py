from app import app, db, Barangay
from datetime import datetime

def add_nabua_barangays():
    with app.app_context():
        # Check if barangays already exist
        if Barangay.query.count() > 0:
            print("Barangays already exist!")
            return
        
        # List of barangays in Nabua (excluding specified ones)
        # Excluded barangays: Angustia, Antipolo Old, Antipolo Young, Inapatan, Aro-Aldow, Bustrac, Dolorosa, Lourdes Old, Paloyon Oriental, Paloyon Sagrada, Salvacion Quigatos, San Antonio Ogbon, San Isidro Inapatan, Malawag
        nabua_barangays = [
            'Duran (Jesus Duran)',
            'La Opinion',
            'La Purisima (La Purisima Agupit)',
            'Lourdes Young',
            'Paloyon Proper (Sagrada Paloyon)',
            'San Antonio (Poblacion)',
            'San Esteban (Poblacion)',
            'San Francisco (Poblacion)',
            'San Isidro (Poblacion)',
            'San Jose (San Jose Pangaraon)',
            'San Juan (Poblacion)',
            'San Luis (Poblacion)',
            'San Miguel (Poblacion)',
            'San Nicolas (Poblacion)',
            'San Roque (Poblacion)',
            'San Roque Madawon',
            'San Roque Sagumay',
            'San Vicente Gorong-Gorong',
            'San Vicente Ogbon',
            'Santa Barbara (Maliban)',
            'Santa Cruz',
            'Santa Elena Baras',
            'Santa Lucia Baras',
            'Santiago Old',
            'Santiago Young',
            'Santo Domingo',
            'Tandaay',
            'Topas Proper',
            'Topas Sogod'
        ]
        
        # Add barangays to database
        added_count = 0
        for i, barangay_name in enumerate(nabua_barangays, 1):
            # Check if barangay already exists
            existing = Barangay.query.filter_by(name=barangay_name).first()
            
            if not existing:
                barangay = Barangay(
                    name=barangay_name,
                    code=f'NBN{i:02d}',  # NBN01, NBN02, etc.
                    municipality='Nabua',
                    province='Camarines Sur',
                    region='Region V (Bicol Region)',
                    is_active=True
                )
                db.session.add(barangay)
                added_count += 1
                print(f"Added: {barangay_name}")
            else:
                print(f"Already exists: {barangay_name}")
        
        db.session.commit()
        print(f"\nSuccessfully added {added_count} new barangays for Nabua!")
        print(f"Total barangays in Nabua: {Barangay.query.count()}")

if __name__ == '__main__':
    add_nabua_barangays()
