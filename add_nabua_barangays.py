from app import app, db, Municipality, Barangay
from datetime import datetime

def add_nabua_barangays():
    with app.app_context():
        # Check if Nabua municipality exists, if not create it
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
        
        # List of all 42 barangays in Nabua
        nabua_barangays = [
            'Angustia (Angustia Inapatan)',
            'Antipolo Old',
            'Antipolo Young',
            'Aro-aldao',
            'Bustrac',
            'Dolorosa (Dolorosa Inapatan)',
            'Duran (Jesus Duran)',
            'Inapatan (Del Rosario Inapatan)',
            'La Opinion',
            'La Purisima (La Purisima Agupit)',
            'Lourdes Old',
            'Lourdes Young',
            'Malawag (San Jose Malawag)',
            'Paloyon Oriental',
            'Paloyon Proper (Sagrada Paloyon)',
            'Salvacion Que Gatos',
            'San Antonio (Poblacion)',
            'San Antonio Ogbon',
            'San Esteban (Poblacion)',
            'San Francisco (Poblacion)',
            'San Isidro (Poblacion)',
            'San Isidro Inapatan',
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
            existing = Barangay.query.filter_by(
                name=barangay_name,
                municipality_id=nabua.id
            ).first()
            
            if not existing:
                barangay = Barangay(
                    name=barangay_name,
                    code=f'NBN{i:02d}',  # NBN01, NBN02, etc.
                    municipality_id=nabua.id,
                    is_active=True
                )
                db.session.add(barangay)
                added_count += 1
                print(f"Added: {barangay_name}")
            else:
                print(f"Already exists: {barangay_name}")
        
        db.session.commit()
        print(f"\nSuccessfully added {added_count} new barangays for Nabua!")
        print(f"Total barangays in Nabua: {Barangay.query.filter_by(municipality_id=nabua.id).count()}")

if __name__ == '__main__':
    add_nabua_barangays()
