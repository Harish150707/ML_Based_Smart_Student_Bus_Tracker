from database import db

if db.is_connected():
    print("✅ Database Connected Successfully!")
else:
    print("❌ Database Connection Failed")