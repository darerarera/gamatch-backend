import random
import re
from flask_mail import Message
from .extensions import mail
import os
from datetime import datetime, timedelta

def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def generate_otp():
    return ''.join([str(random.randint(0, 9)) for _ in range(4)])

def send_verification_email(email, otp):
    msg = Message('GaMatch Account Verification',
                  sender='your_email@gmail.com',
                  recipients=[email])
    msg.body = f'''
    Welcome to GaMatch!
    
    Your verification code is: {otp}
    
    Please use this code to verify your account.
    '''
    mail.send(msg)

def send_reset_email(email, reset_code):
    msg = Message('GaMatch Password Reset',
                  sender='your_email@gmail.com',
                  recipients=[email])
    msg.body = f'''
    Hello!
    
    You have requested to reset your password for your GaMatch account.
    Your password reset code is: {reset_code}
    
    This code will expire in 15 minutes.
    
    If you did not request this reset, please ignore this email.
    '''
    mail.send(msg)

def is_reset_code_expired(expiry_time):
    """Check if reset code has expired"""
    if not expiry_time:
        return True
    return datetime.utcnow() > expiry_time

def generate_reset_code_expiry():
    """Generate expiry timestamp for reset code (15 minutes from now)"""
    return datetime.utcnow() + timedelta(minutes=15)