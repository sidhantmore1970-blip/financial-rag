from core.database import MySession, setup_db
from core import models

roles_data = [
    {"role_name": "Admin", "permissions": "full_access"},
    {"role_name": "Financial Analyst", "permissions": "upload,view,edit"},
    {"role_name": "Auditor", "permissions": "view"},
    {"role_name": "Client", "permissions": "view"},
]


def run_seed():
    setup_db()
    db = MySession()
    try:
        for item in roles_data:
            found = db.query(models.Role).filter(models.Role.role_name == item["role_name"]).first()
            if not found:
                db.add(models.Role(**item))
                print(f"Added role: {item['role_name']}")
            else:
                print(f"Already exists: {item['role_name']}")
        db.commit()
        print("Done seeding roles.")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
