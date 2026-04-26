import requests
from datetime import datetime

# ══════════════════════════════════════════
#  AYARLAR
# ══════════════════════════════════════════
NTFY_TOPIC = "tcdd-bildirim-taylan"
MIN_SAAT   = 14
TARIH      = "30-04-2026"
# ══════════════════════════════════════════

BASE = "https://web-api-prod-ytp.tcddtasimacilik.gov.tr"
CDN  = "https://cdn-api-prod-ytp.tcddtasimacilik.gov.tr"

def token_al():
    # TCDD'nin wsm endpoint'inden token alıyoruz
    url = f"{BASE}/tms/auth/login"
    payload = {"username": "web", "password": ""}
    try:
        r = requests.post(url, json=payload, timeout=15)
        return r.json().get("access_token", "")
    except:
        return ""

def seferleri_getir(token):
    url = f"{BASE}/tms/train/train-availability?environment=dev&userId=1"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "searchRoutes": [{
            "departureStationId": 1325,
            "departureStationName": "İSTANBUL(SÖĞÜTLÜÇEŞME)",
            "arrivalStationId": 98,
            "arrivalStationName": "ANKARA GAR",
            "departureDate": f"{TARIH} 00:00:00"
        }],
        "passengerTypeCounts": [{"id": 0, "count": 1}],
        "searchReservation": False,
        "blTrainTypes": []
    }
    r = requests.post(url, headers=headers, json=payload, timeout=20)
    return r.json()

def ntfy_gonder(mesaj, baslik):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=mesaj.encode("utf-8"),
        headers={"Title": baslik, "Priority": "high", "Tags": "train"}
    )

def kontrol_et():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Kontrol ediliyor...")

    token = token_al()
    if not token:
        print("Token alınamadı, yeniden deneniyor...")
        # Token alınamazsa eski yöntemle devam et
        token = "dummy"

    try:
        data = seferleri_getir(token)
    except Exception as e:
        print(f"HATA: {e}")
        return

    print("API yanıtı:", str(data)[:300])

    bulunanlar = []
    for sefer in data.get("trainAvailabilities", []):
        kalkis_str = sefer.get("departureDate", "")
        try:
            saat = int(kalkis_str[9:11])
        except:
            continue

        if saat < MIN_SAAT:
            continue

        for vagon in sefer.get("wagonAvailabilities", []):
            tur = vagon.get("wagonTypeName", "").lower()
            bos = vagon.get("availableSeatCount", 0)
            if bos > 0 and ("ekonomi" in tur or "business" in tur):
                bulunanlar.append(
                    f"🚆 {kalkis_str[9:14]} — {vagon.get('wagonTypeName','?')} — {bos} koltuk"
                )

    if bulunanlar:
        mesaj = "\n".join(bulunanlar)
        print("BULUNDU:\n" + mesaj)
        ntfy_gonder(mesaj, f"TCDD 30 Nisan — Yer Var!")
    else:
        print("Uygun yer yok.")

if __name__ == "__main__":
    kontrol_et()
