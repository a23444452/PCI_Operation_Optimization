"""Seed script to populate initial configuration data.

Usage: cd backend && python -m app.seed
"""
from app.database import SessionLocal, engine
from app.models.data_management import AttributeItem, MlItem, MslItem, Tank
from app.models.plant import Plant, PlantCriteria
from app.models.user import User
from app.utils.security import hash_password


def seed():
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Plant).first():
            print("Database already seeded. Skipping.")
            return

        # --- Plants ---
        plants = [
            Plant(name="TPE Plant A", code="TPE-A", is_active=True),
            Plant(name="TPE Plant B", code="TPE-B", is_active=True),
            Plant(name="TPE Plant C", code="TPE-C", is_active=True),
        ]
        db.add_all(plants)
        db.flush()

        # --- Plant Criteria ---
        criteria = [
            PlantCriteria(plant_id=plants[0].id, defect_type="Blister", operator="<", threshold=0.005, is_active=True),
            PlantCriteria(plant_id=plants[0].id, defect_type="Cord", operator="<", threshold=0.003, is_active=True),
            PlantCriteria(plant_id=plants[0].id, defect_type="Knot", min_size=0.5, operator="<", threshold=0.002, is_active=True),
            PlantCriteria(plant_id=plants[1].id, defect_type="Blister", operator="<", threshold=0.006, is_active=True),
            PlantCriteria(plant_id=plants[1].id, defect_type="Cord", operator="<", threshold=0.004, is_active=True),
            PlantCriteria(plant_id=plants[2].id, defect_type="Blister", operator="<", threshold=0.004, is_active=True),
            PlantCriteria(plant_id=plants[2].id, defect_type="Stone", operator="<", threshold=0.001, is_active=True),
        ]
        db.add_all(criteria)

        # --- Tanks ---
        tanks = [
            Tank(name="Tank 1", code="T1", is_active=True, sort_order=1),
            Tank(name="Tank 2", code="T2", is_active=True, sort_order=2),
            Tank(name="Tank 3", code="T3", is_active=True, sort_order=3),
            Tank(name="Tank 4", code="T4", is_active=True, sort_order=4),
            Tank(name="Tank 5", code="T5", is_active=True, sort_order=5),
        ]
        db.add_all(tanks)

        # --- ML Items ---
        ml_items = [
            MlItem(name="Blister", display_name="Blister Rate", is_active=True, sort_order=1),
            MlItem(name="Cord", display_name="Cord Rate", is_active=True, sort_order=2),
            MlItem(name="Knot", display_name="Knot Rate", is_active=True, sort_order=3),
            MlItem(name="Stone", display_name="Stone Rate", is_active=True, sort_order=4),
            MlItem(name="Scratch", display_name="Scratch Rate", is_active=True, sort_order=5),
        ]
        db.add_all(ml_items)

        # --- MSL Items ---
        msl_items = [
            MslItem(name="Cord_MSL", display_name="Cord MSL", is_active=True, sort_order=1),
            MslItem(name="Knot_MSL", display_name="Knot MSL", is_active=True, sort_order=2),
            MslItem(name="Stone_MSL", display_name="Stone MSL", is_active=True, sort_order=3),
            MslItem(name="Blister_MSL", display_name="Blister MSL", is_active=True, sort_order=4),
        ]
        db.add_all(msl_items)

        # --- Attribute Items ---
        attr_items = [
            AttributeItem(name="MAX_THICKNESS", display_name="Max Thickness", is_active=True, sort_order=1),
            AttributeItem(name="MIN_THICKNESS", display_name="Min Thickness", is_active=True, sort_order=2),
            AttributeItem(name="TTV", display_name="Total Thickness Variation", is_active=True, sort_order=3),
            AttributeItem(name="WARP", display_name="Warp", is_active=True, sort_order=4),
        ]
        db.add_all(attr_items)

        # --- Default Admin User ---
        admin = User(
            username="admin",
            email="admin@corning.com",
            password_hash=hash_password("admin123"),
            display_name="System Admin",
            role="admin",
            status="active",
        )
        db.add(admin)

        db.commit()
        print("Seed data created successfully!")
        print("  - 3 plants with criteria")
        print("  - 5 tanks")
        print("  - 5 ML items, 4 MSL items, 4 attribute items")
        print("  - Admin user: admin / admin123")

    except Exception as exc:
        db.rollback()
        print(f"Seed failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
