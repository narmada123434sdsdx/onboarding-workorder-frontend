import os
from dotenv import load_dotenv

load_dotenv()
print(os.getenv("DATABASE_URL"))

class Config:
    # DB_CONFIG = {
    #     'host': os.getenv('DB_HOST'),
    #     'port': os.getenv('DB_PORT'),
    #     'user': os.getenv('DB_USER'),
    #     'password': os.getenv('DB_PASSWORD'),
    #     'database': os.getenv('DB_NAME')
    # }
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")  # Must be set in .env
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    EMAIL_CONFIG = {
        'sender_email': os.getenv('SMTP_USER'),
        'sender_password': os.getenv('SMTP_PASSWORD'),
        'smtp_server': os.getenv('SMTP_HOST'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587))
    }

    # ✅ Add this line
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'prathipatiramya2003@gmail.com')

    # ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173')
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")


    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'cvI_hj-yDtPL1Z2lFlRBTBzTE72Hw1U0DTKw2U5uh3s=')
    UPLOAD_FOLDER = 'backend/uploads'
