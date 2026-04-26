import requests
from datetime import datetime

# ══════════════════════════════════════════
NTFY_TOPIC = "tcdd-bildirim-taylan"
MIN_SAAT   = 14
TARIH      = "30-04-2026"
TOKEN      = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJlVFFicDhDMmpiakp1cnUzQVk2a0ZnV196U29MQXZIMmJ5bTJ2OUg5THhRIn0.eyJleHAiOjE3MjEzODQ0NzAsImlhdCI6MTcyMTM4NDQxMCwianRpIjoiYWFlNjVkNzgtNmRkZS00ZGY4LWEwZWYtYjRkNzZiYjZlODNjIiwiaXNzIjoiaHR0cDovL3l0cC1wcm9kLW1hc3RlcjEudGNkZHRhc2ltYWNpbGlrLmdvdi50cjo4MDgwL3JlYWxtcy9tYXN0ZXIiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiMDAzNDI3MmMtNTc2Yi00OTBlLWJhOTgtNTFkMzc1NWNhYjA3IiwidHlwIjoiQmVhcmVyIiwiYXpwIjoidG1zIiwic2Vzc2lvbl9zdGF0ZSI6IjAwYzM4NTJiLTg1YjEtNDMxNS04OGIwLWQ0MWMxMTcyYzA0MSIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsiZGVmYXVsdC1yb2xlcy1tYXN0ZXIiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgZW1haWwgcHJvZmlsZSIsInNpZCI6IjAwYzM4NTJiLTg1YjEtNDMxNS04OGIwLWQ0MWMxMTcyYzA0MSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwicHJlZmVycmVkX3VzZXJuYW1lIjoid2ViIiwiZ2l2ZW5fbmFtZSI6IiIsImZhbWlseV9uYW1lIjoiIn0.AIW_4Qws2wfwxyVg8dgHRT9jB3qNavob2C4mEQIQGl3urzW2jALPx-e51ZwHUb-TXB-X2RPHakonxKnWG6tDIP5aKhiidzXDcr6pDDoYU5DnQhMg1kywyOaMXsjLFjuYN5PAyGUMh6YSOVsg1PzNh-5GrJF44pS47JnB9zk03Pr08napjsZPoRB-5N4GQ49cnx7ePC82Y7YIc-gTew2baqKQPz9_v381Gbm2V38PZDH9KldlcWut7kqQYJFMJ7dkM_entPJn9lFk7R5h5j_06OlQEpWRMQTn9SQ1AYxxmZxBu5XYMKDkn4rzIIVCkdTPJNCt5PvjENjClKFeUA1DOg"
# ══════════════════════════════════════════

def seferleri_getir():
    url = "https://web-api-prod-ytp.tcddtasimacilik.gov.tr/tms/train/train-availability?environment=dev&userId=1"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}"
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
    try:
        data = seferleri_getir()
    except Exception as e:
        print(f"HATA: {e}")
        return

    bulunanlar = []
    for leg in data.get("trainLegs", []):
        for availability in leg.get("trainAvailabilities", []):
            for train in availability.get("trains", []):
                # Kalkış saatini segment'ten al
                segments = train.get("segments", [])
                if not segments:
                    continue
                kalkis_ms = segments[0].get("departureTime", 0)
                kalkis_dt = datetime.fromtimestamp(kalkis_ms / 1000)
                
                if kalkis_dt.hour < MIN_SAAT:
                    continue

                # Koltuk kapasitelerini kontrol et
                # bookingClassId: 1=Ekonomi, 4=Business
                for koltuk in train.get("bookingClassCapacities", []):
                    sinif_id = koltuk.get("bookingClassId")
                    kapasite = koltuk.get("capacity", 0)
                    sinif_adi = "Ekonomi" if sinif_id == 1 else "Business" if sinif_id == 4 else None
                    
                    if sinif_adi and kapasite > 0:
                        bulunanlar.append(
                            f"🚆 {kalkis_dt.strftime('%H:%M')} — {train.get('name','?')} — {sinif_adi} — {kapasite} koltuk"
                        )

    if bulunanlar:
        mesaj = "\n".join(bulunanlar)
        print("BULUNDU:\n" + mesaj)
        ntfy_gonder(mesaj, "TCDD 30 Nisan — Yer Var!")
    else:
        print("Uygun yer yok.")

if __name__ == "__main__":
    kontrol_et()
