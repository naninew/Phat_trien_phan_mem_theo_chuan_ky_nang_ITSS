import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.database import SessionLocal
from app.models.review import Review
from app.models.company import RescueCompany
from app.models.user import User
from app.models.request import RescueRequest
from datetime import datetime, timedelta

def seed_reviews():
    db = SessionLocal()
    try:
        # Get the first company
        company = db.query(RescueCompany).first()
        if not company:
            print("No company found.")
            return

        # Get first customer
        customer = db.query(User).filter(User.role == "customer").first()
        if not customer:
            print("No customer found.")
            return
            
        # Get or create 3 dummy rescue requests for this company to attach reviews
        requests = db.query(RescueRequest).filter(RescueRequest.company_id == company.id).limit(3).all()
        
        while len(requests) < 3:
            req = RescueRequest(
                user_id=customer.id,
                company_id=company.id,
                status="COMPLETED",
                incident_type="Xe chết máy",
                latitude=21.0285,
                longitude=105.8542,
                address_description="Hoàn Kiếm, Hà Nội"
            )
            db.add(req)
            db.commit()
            db.refresh(req)
            requests.append(req)
            
        # Check existing reviews
        for i, req in enumerate(requests):
            existing = db.query(Review).filter(Review.rescue_request_id == req.id).first()
            if not existing:
                ratings = [5, 4, 5]
                comments = [
                    "Dịch vụ rất tốt, nhân viên nhiệt tình, đến rất nhanh! Cảm ơn công ty nhiều.",
                    "Giá cả hợp lý, xử lý sự cố khá chuyên nghiệp.",
                    "Tuyệt vời! Gọi cái là có mặt liền trong đêm tối, rất yên tâm."
                ]
                rev = Review(
                    rescue_request_id=req.id,
                    user_id=customer.id,
                    company_id=company.id,
                    rating=ratings[i],
                    comment=comments[i],
                    created_at=datetime.utcnow() - timedelta(days=i)
                )
                db.add(rev)
                
        db.commit()
        print("Successfully seeded reviews!")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_reviews()
