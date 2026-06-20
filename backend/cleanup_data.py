import sys
import os

# Add backend directory to sys.path to be able to import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.company import RescueCompany
from app.models.request import RescueRequest
from app.models.review import Review
from app.models.user import User

def main():
    db = SessionLocal()
    print("Cleaning up database...")

    # 1. Update pending companies: delete requests and reviews for them
    pending_companies = db.query(RescueCompany).filter(RescueCompany.status == "pending").all()
    for company in pending_companies:
        print(f"Cleaning up pending company: {company.company_name} (ID: {company.id})")
        
        # Delete requests
        req_deleted = db.query(RescueRequest).filter(RescueRequest.company_id == company.id).delete()
        if req_deleted > 0:
            print(f"  - Deleted {req_deleted} invalid requests")
            
        # Delete reviews
        rev_deleted = db.query(Review).filter(Review.company_id == company.id).delete()
        if rev_deleted > 0:
            print(f"  - Deleted {rev_deleted} invalid reviews")
            
    db.commit()

    # 2. Fix fake names in users
    users = db.query(User).all()
    for user in users:
        fname = (user.full_name or "").lower()
        if "công ty" in fname and any(char.isdigit() for char in fname):
            print(f"User {user.id} has fake name: {user.full_name}")
            if user.role.value == "company_staff":
                company = db.query(RescueCompany).filter(RescueCompany.owner_id == user.id).first()
                if company:
                    new_name = company.representative_name or company.company_name
                    if new_name:
                        print(f"  -> Updating to {new_name}")
                        user.full_name = new_name
                        db.commit()
            
    print("Cleanup completed.")
    db.close()

if __name__ == "__main__":
    main()
