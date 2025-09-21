from app import app, db, Municipality, Barangay, WasteItem, CollectionRoute, WasteTracking
from datetime import datetime

def cleanup_municipalities():
    with app.app_context():
        # Keep only Nabua municipality
        nabua = Municipality.query.filter_by(name='Nabua').first()
        
        if not nabua:
            print("Nabua municipality not found!")
            return
        
        print(f"Keeping municipality: {nabua.name}, {nabua.province}")
        
        # Get all other municipalities
        other_municipalities = Municipality.query.filter(Municipality.id != nabua.id).all()
        
        if not other_municipalities:
            print("No other municipalities to remove.")
            return
        
        print(f"Found {len(other_municipalities)} other municipalities to remove:")
        for mun in other_municipalities:
            print(f"  - {mun.name}, {mun.province}")
        
        # Get all barangays from other municipalities
        other_barangay_ids = []
        for mun in other_municipalities:
            barangays = Barangay.query.filter_by(municipality_id=mun.id).all()
            other_barangay_ids.extend([b.id for b in barangays])
            print(f"  - {mun.name}: {len(barangays)} barangays")
        
        # Check if there are any waste items from other municipalities
        waste_items_count = WasteItem.query.filter(WasteItem.barangay_id.in_(other_barangay_ids)).count()
        if waste_items_count > 0:
            print(f"\nWARNING: Found {waste_items_count} waste items from other municipalities!")
            print("These will also be deleted. Continue? (y/n): ", end="")
            response = input().lower()
            if response != 'y':
                print("Operation cancelled.")
                return
        
        # Delete waste tracking records for other municipalities
        tracking_count = 0
        for barangay_id in other_barangay_ids:
            tracking_records = WasteTracking.query.join(WasteItem).filter(WasteItem.barangay_id == barangay_id).all()
            tracking_count += len(tracking_records)
            for record in tracking_records:
                db.session.delete(record)
        
        # Delete waste items from other municipalities
        waste_items = WasteItem.query.filter(WasteItem.barangay_id.in_(other_barangay_ids)).all()
        for item in waste_items:
            db.session.delete(item)
        
        # Delete collection routes for other municipalities
        collection_routes = CollectionRoute.query.filter(CollectionRoute.barangay_id.in_(other_barangay_ids)).all()
        for route in collection_routes:
            db.session.delete(route)
        
        # Delete barangays from other municipalities
        barangays = Barangay.query.filter(Barangay.municipality_id.in_([m.id for m in other_municipalities])).all()
        for barangay in barangays:
            db.session.delete(barangay)
        
        # Delete other municipalities
        for mun in other_municipalities:
            db.session.delete(mun)
        
        # Commit all changes
        db.session.commit()
        
        print(f"\nCleanup completed!")
        print(f"Removed {len(other_municipalities)} municipalities")
        print(f"Removed {len(barangays)} barangays")
        print(f"Removed {len(waste_items)} waste items")
        print(f"Removed {tracking_count} tracking records")
        print(f"Removed {len(collection_routes)} collection routes")
        
        # Show remaining data
        remaining_municipalities = Municipality.query.all()
        remaining_barangays = Barangay.query.all()
        remaining_waste_items = WasteItem.query.count()
        
        print(f"\nRemaining data:")
        print(f"- Municipalities: {len(remaining_municipalities)}")
        print(f"- Barangays: {len(remaining_barangays)}")
        print(f"- Waste items: {remaining_waste_items}")
        
        if remaining_municipalities:
            print(f"\nRemaining municipality: {remaining_municipalities[0].name}, {remaining_municipalities[0].province}")
            print(f"Barangays in {remaining_municipalities[0].name}:")
            for barangay in remaining_barangays:
                print(f"  - {barangay.name}")

if __name__ == '__main__':
    cleanup_municipalities()
