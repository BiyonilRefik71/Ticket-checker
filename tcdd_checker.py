import requests
import json
from datetime import datetime

# ══════════════════════════════════════════
#  AYARLAR — sadece burayı düzenle
# ══════════════════════════════════════════
NTFY_TOPIC = "tcdd-bildirim-taylan"   # ntfy'da abone olduğun kanal adı
MIN_SAAT   = 14                        # saat 14'ten sonraki trenler
TARIH      = "2026-04-30"
BINIS      = "İstanbul(Söğütlüçeşme)"
INIS       = "Ankara Gar"
# ══════════════════════════════════════════

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Basic dGNkZDpkZW1pcnlvbHU="
}

def istasyon_id_al(ad):
    url = "https://api-ytp.tcddtasimacilik.gov.tr/sacip/api/station/getall"
    r = requests.get(url, headers=HEADERS, timeout=15)
    for s in r.json():
        if s.get("stationName", "").strip() == ad.strip():
            return s["stationId"]
    raise ValueError(f"İstasyon bulunamadı: {ad}")

def seferleri_getir(binis_id, inis_id, tarih):
    url = "https://api-ytp.tcddtasimacilik.gov.tr/sacip/api/journey/search"
    payload = {
        "departureStationId": binis_id,
        "arrivalStationId": inis_id,
        "departureDate": tarih + "T00:00:00",
        "passengerCount": 1,
        "isPromoApplied": False
    }
    r = requests.post(url, headers=HEADERS, json=payload, timeout=20)
    return r.json()

def ntfy_gonder(mesaj, baslik):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=mesaj.encode("utf-8"),
        headers={"Title": baslik, "Priority": "high", "Tags": "train"}
    )

def kontrol_et():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Kontrol ediliyor...")
    
    try:
        binis_id = istasyon_id_al(BINIS)
        inis_id  = istasyon_id_al(INIS)
        data     = seferleri_getir(binis_id, inis_id, TARIH)
    except Exception as e:
        print(f"HATA: {e}")
        return

    bulunanlar = []

    for sefer in data.get("journeyList", []):
        kalkis_str = sefer.get("departureTime", "")
        try:
            kalkis_saat = int(kalkis_str[11:13])  # "2026-04-30T14:30:00" → 14
        except:
            continue

        if kalkis_saat < MIN_SAAT:
            continue

        for vagon in sefer.get("wagons", []):
            tur = vagon.get("wagonType", "").lower()
            bos = vagon.get("availableSeatCount", 0)

            if bos > 0 and ("ekonomi" in tur or "business" in tur or "ekonomik" in tur):
                bulunanlar.append(
                    f"🚆 {kalkis_str[11:16]} — {vagon.get('wagonTypeName','?')} — {bos} koltuk boş"
                )

    if bulunanlar:
        mesaj = "\n".join(bulunanlar)
        print("BULUNDU:\n" + mesaj)
        ntfy_gonder(mesaj, f"TCDD {TARIH} — Yer Var!")
    else:
        print("Uygun yer yok.")

if __name__ == "__main__":
    kontrol_et()
