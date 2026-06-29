# billing/otp.py
import random
from django.core.cache import cache
from django.conf import settings
from twilio.rest import Client


def generate_otp():
    return str(random.randint(100000, 999999))


def get_otp_cache_key(customer_code):
    return f"otp:{customer_code}"


def get_attempts_cache_key(customer_code):
    return f"otp_attempts:{customer_code}"


def send_otp_via_whatsapp(phone_number, otp_code):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        to=f'whatsapp:{phone_number}',
        body=f"Your verification code is {otp_code}. It expires in 5 minutes. Do not share this code."
    )
    return message.sid


def create_and_send_otp(customer):
    otp_code = generate_otp()
    cache_key = get_otp_cache_key(customer.customer_code)

    cache.set(cache_key, otp_code, timeout=settings.OTP_EXPIRY_SECONDS)
    cache.set(get_attempts_cache_key(customer.customer_code), 0, timeout=settings.OTP_EXPIRY_SECONDS)

    send_otp_via_whatsapp(customer.phone, otp_code)
    return True


def verify_otp(customer_code, submitted_code):
    cache_key = get_otp_cache_key(customer_code)
    attempts_key = get_attempts_cache_key(customer_code)

    stored_code = cache.get(cache_key)
    attempts = cache.get(attempts_key, 0)

    if stored_code is None:
        return False, "OTP expired or not requested. Please request a new code."

    if attempts >= settings.OTP_MAX_ATTEMPTS:
        cache.delete(cache_key)
        return False, "Too many incorrect attempts. Please request a new code."

    if submitted_code != stored_code:
        cache.set(attempts_key, attempts + 1, timeout=settings.OTP_EXPIRY_SECONDS)
        return False, "Incorrect code. Please try again."

    cache.delete(cache_key)
    cache.delete(attempts_key)
    return True, "Verified"