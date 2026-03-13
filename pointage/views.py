import re, time, uuid, base64, binascii
from django.http import JsonResponse
from django.shortcuts import render
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

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

def index(request):
    return render(request, 'pointage/index.html')

def get_pointages(request):
    try:
        session = requests.Session()
        session.get("https://vtportal.visualtime.net/2/indexv2.aspx",
                    headers={"User-Agent": "Mozilla/5.0"})

        guid_token    = str(uuid.uuid4())
        encrypted_pwd = encrypt_password(PASSWORD)

        resp = session.post(f"{BASE_URL}/Authenticate", files={
            "user":          (None, USER),
            "password":      (None, encrypted_pwd),
            "language":      (None, "ESP"),
            "accessFromApp": (None, "false"),
            "appVersion":    (None, "3.46.0"),
            "validationCode":(None, ""),
            "timeZone":      (None, "Europe/Madrid"),
            "buttonLogin":   (None, "true"),
        }, headers={
            "Roapp": "VTPortal", "Roauth": guid_token,
            "Rocompanyid": "reci3686", "Rosrc": "false",
            "Rotoken": "", "X-Requested-With": "XMLHttpRequest",
        })

        result = resp.json().get("d", {})
        if result.get("Status") != 0:
            return JsonResponse({"error": "Connexion VTPortal échouée"})

        token = result["Token"]
        headers_api = {
            "Roapp": "VTPortal", "Roauth": guid_token,
            "Rocompanyid": "reci3686", "Rosrc": "false",
            "Rotoken": token, "X-Requested-With": "XMLHttpRequest",
        }

        today = datetime.now().strftime("%d/%m/%Y")
        punches_resp = session.get(
            f"{BASE_URL}/GetMyPunches",
            params={"selectedDate": today, "timestamp": int(time.time())},
            headers=headers_api
        )

        raw = punches_resp.json().get("d", {}).get("Punches", [])
        punches = []
        entry_count = 0
        for p in raw:
            ms = int(re.search(r'\d+', p["DateTime"]).group())
            dt = datetime.fromtimestamp(ms / 1000)

            punch_type = p["Type"]
            if punch_type == 1:
                entry_count += 1
                if entry_count == 2:
                    punch_type = 3

            punches.append({
                "type":     punch_type,
                "time":     dt.strftime("%H:%M:%S"),
                "terminal": p.get("TerminalName", ""),
            })

        return JsonResponse({"punches": punches})

    except Exception as e:
        return JsonResponse({"error": str(e)})