import requests, base64, time, json, binascii, uuid
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
USER     = os.getenv("VT_USER")
PASSWORD = os.getenv("VT_PASSWORD")
BASE_URL = "https://vtportal.visualtime.net/api/portalsvcx.svc"

def encrypt_password(password):
    key = binascii.unhexlify("152a3243b4157617c81f2a6b1c2d3e4f")
    iv  = binascii.unhexlify("101a12641415161713391a1c1c1d9e1f")
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(password.encode("utf-8"), AES.block_size))
    return base64.b64encode(encrypted).decode("utf-8")

def get_pointages():
    session = requests.Session()

    print("Chargement de la page login...")
    session.get(
        "https://vtportal.visualtime.net/2/indexv2.aspx",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )

    # Générer un GUID comme le fait le navigateur
    guid_token = str(uuid.uuid4())
    print(f"GUID généré : {guid_token}")

    encrypted_pwd = encrypt_password(PASSWORD)
    print(f"Mot de passe chiffré : {encrypted_pwd}")

    headers = {
        "Accept": "*/*",
        "Origin": "https://vtportal.visualtime.net",
        "Referer": "https://vtportal.visualtime.net/2/indexv2.aspx",
        "Roapp": "VTPortal",
        "Roauth": guid_token,
        "Rocompanyid": "reci3686",
        "Rosrc": "false",
        "Rotoken": "",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    form_data = {
        "user":          (None, USER),
        "password":      (None, encrypted_pwd),
        "language":      (None, "ESP"),
        "accessFromApp": (None, "false"),
        "appVersion":    (None, "3.46.0"),
        "validationCode":(None, ""),
        "timeZone":      (None, "Europe/Madrid"),
        "buttonLogin":   (None, "true"),
    }

    print("Connexion à VTPortal...")
    response = session.post(
        f"{BASE_URL}/Authenticate",
        files=form_data,
        headers=headers
    )

    print(f"HTTP status : {response.status_code}")
    result = response.json().get("d", {})
    status = result.get("Status")
    token  = result.get("Token", "")
    roauth = result.get("UserId", "")

    print(f"Status connexion : {status}")

    if status != 0:
        print("❌ Connexion échouée !")
        return

    print(f"✅ Connecté ! Token : {token[:30]}...")

    headers_api = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Roapp": "VTPortal",
        "Roauth": guid_token,        # ← le GUID, pas roauth/UserId
        "Rocompanyid": "reci3686",
        "Rosrc": "false",
        "Rotoken": token,
        "X-Requested-With": "XMLHttpRequest"
    }

    today = datetime.now().strftime("%d/%m/%Y")
    timestamp = int(time.time())
    print(f"\nPointages du {today} :\n")

    punches = session.get(
        f"{BASE_URL}/GetMyPunches",
        params={"selectedDate": today, "timestamp": timestamp},
        headers=headers_api
    )

    data = punches.json().get("d", {})
    
    types = {1: "🟢 Entrée", 2: "🟡 Pause", 3: "🔵 Retour", 4: "🔴 Sortie"}

    for punch in data.get("Punches", []):
        # Convertir /Date(1773385928000+0100)/ en heure lisible
        import re
        ms = int(re.search(r'\d+', punch["DateTime"]).group())
        dt = datetime.fromtimestamp(ms / 1000)
        type_label = types.get(punch["Type"], f"Type {punch['Type']}")
        print(f"  {type_label} — {dt.strftime('%H:%M:%S')}")

if __name__ == "__main__":
    get_pointages()