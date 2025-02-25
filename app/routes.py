from flask import Blueprint, request, jsonify
from flask_cors import CORS  # Add this import
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from .extensions import db  # Impor db dari extensions.py
from .utils import (
    is_valid_email, 
    generate_otp, 
    send_verification_email, 
    send_reset_email,
    is_reset_code_expired,
    generate_reset_code_expiry
)
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint('auth', __name__)
CORS(auth_bp)  # Add this line

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate input
    if not data.get('nama') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'All fields are required'}), 400
    
    if len(data['password']) < 8:
        return jsonify({'message': 'Password must be at least 8 characters'}), 400
    
    if not is_valid_email(data['email']):
        return jsonify({'message': 'Invalid email format'}), 400

    try:
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'message': 'Email already registered'}), 400

        # Generate OTP
        verification_code = generate_otp()

        # Create new user
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            nama=data['nama'], 
            email=data['email'], 
            password=hashed_password,
            verification_code=verification_code,
            is_verified=False
        )

        db.session.add(new_user)
        db.session.commit()

        # Send verification email
        send_verification_email(data['email'], verification_code)

        return jsonify({'message': 'Registration successful, please verify your email'}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Registration failed'}), 500

@auth_bp.route('/verify', methods=['POST'])
def verify_account():
    data = request.get_json()
    
    user = User.query.filter_by(email=data.get('email')).first()
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if user.is_verified:
        return jsonify({'message': 'Account already verified'}), 400
    
    if user.verification_code != data.get('code'):
        return jsonify({'message': 'Invalid verification code'}), 400
    
    # Mark user as verified
    user.is_verified = True
    user.verification_code = None
    db.session.commit()
    
    return jsonify({'message': 'Account verified successfully'}), 200

@auth_bp.route('/resend-code', methods=['POST'])
def resend_verification_code():
    data = request.get_json()
    
    user = User.query.filter_by(email=data.get('email')).first()
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if user.is_verified:
        return jsonify({'message': 'Account already verified'}), 400
    
    # Generate new OTP
    new_verification_code = generate_otp()
    user.verification_code = new_verification_code
    db.session.commit()
    
    # Send new verification email
    send_verification_email(user.email, new_verification_code)
    
    return jsonify({'message': 'New verification code sent'}), 200

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()

    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid email or password'}), 401
    
    if not user.is_verified:
        return jsonify({'message': 'Please verify your email first'}), 403
    
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'nama': user.nama,
            'email': user.email
        }
    }), 200

@auth_bp.route('/request-reset', methods=['POST'])
def request_password_reset():
    """Handle the initial password reset request without CAPTCHA verification"""
    data = request.get_json()

    if not data.get('email'):
        return jsonify({'message': 'Email is required'}), 400
    
    # Validate email format
    if not is_valid_email(data['email']):
        return jsonify({'message': 'Invalid email format'}), 400

    user = User.query.filter_by(email=data['email']).first()
    if not user:
        # Don't reveal whether the email exists
        return jsonify({'message': 'If the email exists, a reset code will be sent'}), 200
    
    # Generate and save reset code
    reset_code = generate_otp()
    user.reset_code = reset_code
    user.reset_code_expiry = generate_reset_code_expiry()

    try:
        db.session.commit()
        # Send reset email
        send_reset_email(user.email, reset_code)
        return jsonify({'message': 'Reset code has been sent to your email'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to process request'}), 500

@auth_bp.route('/verify-reset-code', methods=['POST'])
def verify_reset_code():
    """Verify the reset code entered by the user"""
    data = request.get_json()

    if not data.get('email') or not data.get('code'):
        return jsonify({'message': 'Email and reset code are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        return jsonify({'message': 'Invalid reset code'}), 400
    
    if not user.reset_code or user.reset_code != data['code']:
        return jsonify({'message': 'Invalid reset code'}), 400
    
    if is_reset_code_expired(user.reset_code_expiry):
        return jsonify({'message': 'Reset code has expired'}), 400
    
    return jsonify({'message': 'Reset code verified successfully'}), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset the user's password after code verification"""
    data = request.get_json()

    if not all(key in data for key in ['email', 'code', 'new_password']):
        return jsonify({'message': 'All fields are required'}), 400
    
    if len(data['new_password']) < 8:
        return jsonify({'message': 'Password must be at least 8 characters'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        return jsonify({'message': 'Invalid reset code'}), 400
    
    if not user.reset_code or user.reset_code != data['code']:
        return jsonify({'message': 'Invalid reset code'}), 400
    
    if is_reset_code_expired(user.reset_code_expiry):
        return jsonify({'message': 'Reset code has expired'}), 400
    
    try:
        # Update password and clear reset code
        user.password = generate_password_hash(data['new_password'])
        user.reset_code = None
        user.reset_code_expiry = None
        db.session.commit()

        return jsonify({'message': 'Password has been reset successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to reset password'}), 500