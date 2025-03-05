from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import stripe
from config import db

payment = Blueprint('payment', __name__)

@payment.route('/pay', methods=['POST'])
@jwt_required()
def create_payment():
    """Creates a Stripe payment session"""
    user = get_jwt_identity()
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': 'Premium Storage'},
                'unit_amount': 999,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url="http://localhost:5000/success",
        cancel_url="http://localhost:5000/cancel"
    )
    
    return jsonify({"checkout_url": session.url})

@payment.route('/success', methods=['GET'])
@jwt_required()
def payment_success():
    """Upgrades user to premium after payment"""
    user = get_jwt_identity()

    with db.cursor() as cursor:
        cursor.execute("UPDATE users SET is_premium = TRUE WHERE id = %s", (user['id'],))
        db.commit()

    return jsonify({"message": "Payment successful, you are now a premium user!"})
