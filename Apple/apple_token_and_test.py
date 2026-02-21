import httpx
import jwt
import time

# --- Configuration ---
TEAM_ID = "DH3467C58U"       # From Step 1
KEY_ID = "3CXU6RHQ6R"         # From Step 3
KEY_FILE = "C:\shared\Dev\kilo_ai\RSS_Feed\Apple\AuthKey_3CXU6RHQ6R.p8" # Path to your downloaded .p8 file

def generate_token() -> str:
    with open(KEY_FILE, "r") as f:
        private_key = f.read()

    payload = {
        "iss": TEAM_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + (3600 * 24 * 30),  # 30 days
    }
    return jwt.encode(
        payload,
        private_key,
        algorithm="ES256",
        headers={"kid": KEY_ID},
    )

def test_token(token: str):
    base_url = "https://api.music.apple.com/v1"
    headers = {"Authorization": f"Bearer {token}"}

    tests = {
        "Search for 'Radiohead'": f"{base_url}/catalog/us/search?term=radiohead&types=artists&limit=1",
        "Fetch album by ID (OK Computer)": f"{base_url}/catalog/us/albums/1097862870",
        "Fetch song by ID (Creep)": f"{base_url}/catalog/us/songs/1234506727",
    }

    with httpx.Client(headers=headers, timeout=10) as client:
        for label, url in tests.items():
            try:
                response = client.get(url)
                status = response.status_code
                if status == 200:
                    data = response.json().get("data") or response.json().get("results")
                    print(f"✅ {label} — {status} OK | Got: {data}")
                else:
                    print(f"❌ {label} — {status} | Body: {response.text[:200]}")
            except httpx.RequestError as e:
                print(f"💥 {label} — Request failed: {e}")

if __name__ == "__main__":
    print("Generating token...")
    token = generate_token()
    print(f"Token (first 60 chars): {token[:60]}...\n")
    print("Running API tests...\n")
    test_token(token)
