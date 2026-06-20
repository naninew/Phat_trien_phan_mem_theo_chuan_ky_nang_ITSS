"""
Backend run script.
"""
from app.main import app

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Roadside Assistance System API...")
    print("API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
