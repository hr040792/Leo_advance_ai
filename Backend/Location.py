# location.py
import geocoder

def get_current_location():
    g = geocoder.ip('me')  # Fetch location based on your IP address
    return g # Returns the latitude and longitude
