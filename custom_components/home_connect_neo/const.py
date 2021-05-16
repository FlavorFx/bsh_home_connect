"""Constants for the Home Connect integration."""

DOMAIN = "home_connect_neo"
NAME = "Home Connect Neo"

# BASE_URL = "https://api.home-connect.com"
BASE_URL = "https://simulator.home-connect.com"

ENDPOINT_AUTHORIZE = "/security/oauth/authorize"
ENDPOINT_TOKEN = "/security/oauth/token"
ENDPOINT_APPLIANCES = "/api/homeappliances"

SIGNAL_UPDATE_ENTITIES = "home_connect_neo.update_entities"
