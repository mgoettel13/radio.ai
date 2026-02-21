import jwt
import time

# --- Configuration ---
TEAM_ID = "DH3467C58U"       # From Step 1
KEY_ID = "3CXU6RHQ6R"         # From Step 3
KEY_FILE = "C:\shared\Dev\kilo_ai\RSS_Feed\Apple\AuthKey_3CXU6RHQ6R.p8" # Path to your downloaded .p8 file

def generate_music_token():
    with open(KEY_FILE, 'r') as f:
        private_key = f.read()

    headers = {
        "alg": "ES256",
        "kid": KEY_ID
    }

    payload = {
        "iss": TEAM_ID,  # Issuer: Your Team ID
        "iat": int(time.time()),  # Issued At: Current time
        "exp": int(time.time()) + (3600 * 24 * 30)  # Expiration: 30 days (max 6 months)
    }

    token = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
    return token

if __name__ == "__main__":
    try:
        token = generate_music_token()
        print(f"Bearer {token}")
    except Exception as e:
        print(f"Error: {e}")
