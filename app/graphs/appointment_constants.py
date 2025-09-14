"""
Constants and templates for appointment booking graph
"""

def get_booking_confirmation_template(booking: dict) -> str:
    """Get booking confirmation message template"""
    return f"""✅ Your appointment is confirmed!

📍 {booking.get('provider_name', 'Provider')}
💇 {booking.get('service_name', 'Service')}
📅 {booking.get('start_time', 'Time')}
🎫 Confirmation: {booking.get('confirmation_code', 'N/A')}

You'll receive a confirmation SMS shortly."""


DEFAULT_HELP_MESSAGE = "I can help you book appointments. Try saying 'Book me a haircut tomorrow at 2pm'"