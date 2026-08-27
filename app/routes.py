"""HTTP arayüz katmanı (API rotaları).

Separation of Concerns: Bu modül yalnızca üç işi yapar:
  1. Gelen isteğin gövdesini doğrulamak,
  2. İşi ilgili servise (`services/ai_service.py`) veya veritabanı katmanına
     (`app/database.py`) devretmek,
  3. Sonucu tutarlı bir JSON sözleşmesiyle döndürmek.

Burada ham SQL sorgusu, harici API çağrısı veya iş kuralı hesabı yer almaz.

Gizlilik: Hiçbir durumda iç hata izleri (traceback) istemciye gönderilmez;
ayrıntılar yalnızca sunucu günlüğüne yazılır.
"""

import re

from flask import Blueprint, current_app, jsonify, request

from app import database
from services.ai_service import AIServiceError, ai_service

api_bp = Blueprint("api", __name__)

# Telefon numarası için esnek doğrulama: rakam, boşluk, +, -, parantez.
TELEFON_DESENI = re.compile(r"^[0-9+\-\s()]{7,25}$")

# Serbest metin alanları için üst sınırlar (kötüye kullanımı sınırlar).
ISIM_MAX = 120
TELEFON_MAX = 25
MESAJ_MAX = 2000


def _hata(mesaj, durum):
    """Standart hata yanıtı üretir.

    Args:
        mesaj (str): Teknik detay içermeyen, kullanıcıya gösterilebilir metin.
        durum (int): HTTP durum kodu.

    Returns:
        tuple: (Flask response, durum kodu)
    """
    return jsonify({"basari": False, "hata": mesaj}), durum


def _govde_al():
    """İstek gövdesini JSON sözlüğü olarak döndürür.

    Gövde eksik veya geçersizse boş sözlük döner; böylece doğrulama akışı
    istisna fırlatmadan devam eder.

    Returns:
        dict: Ayrıştırılmış JSON gövdesi.
    """
    veri = request.get_json(silent=True)
    return veri if isinstance(veri, dict) else {}


def _metin(veri, alan, sinir):
    """Belirtilen alanı kırpılmış ve uzunluğu sınırlanmış metin olarak alır.

    Args:
        veri (dict): İstek gövdesi.
        alan (str): Okunacak alan adı.
        sinir (int): İzin verilen maksimum karakter sayısı.

    Returns:
        str: Temizlenmiş metin (alan yoksa boş string).
    """
    deger = veri.get(alan)
    if not isinstance(deger, str):
        return ""
    return deger.strip()[:sinir]


# ----------------------------------------------------------------------
# Sohbet
# ----------------------------------------------------------------------
@api_bp.route("/sohbet", methods=["POST"])
def sohbet():
    """Müşteri mesajına yapay zekâ asistanı yanıtı döndürür.

    İstek gövdesi:
        {"mesaj": "Glütensiz pastanız var mı?", "gecmis": [...]}

    Yanıtlar:
        200: {"basari": true, "cevap": "..."}
        400: Mesaj boş veya geçersiz.
        503: AI servisi geçici olarak kullanılamıyor.
    """
    veri = _govde_al()
    mesaj = _metin(veri, "mesaj", current_app.config["MAX_MESSAGE_LENGTH"])

    if not mesaj:
        return _hata("'mesaj' alanı zorunludur ve boş olamaz.", 400)

    gecmis = veri.get("gecmis")
    if gecmis is not None and not isinstance(gecmis, list):
        return _hata("'gecmis' alanı bir liste olmalıdır.", 400)

    try:
        cevap = ai_service.yanit_uret(mesaj, gecmis)
    except AIServiceError as hata:
        # Servis kaynaklı, beklenen bir arıza: 503 Service Unavailable.
        current_app.logger.warning("AI servisi kullanılamıyor: %s", hata)
        return _hata(
            "Akıllı asistan şu anda yanıt veremiyor. Lütfen kısa bir süre "
            "sonra tekrar deneyin veya iletişim bilgilerinizi bırakın.",
            503,
        )
    except Exception:  # noqa: BLE001 - beklenmeyen hatalar da sızdırılmamalı
        current_app.logger.exception("Sohbet isteğinde beklenmeyen hata.")
        return _hata("Beklenmeyen bir hata oluştu.", 500)

    return jsonify({"basari": True, "cevap": cevap}), 200


# ----------------------------------------------------------------------
# Müşteri adayları (leads)
# ----------------------------------------------------------------------
@api_bp.route("/leads", methods=["POST"])
def lead_olustur():
    """Yeni bir müşteri adayı kaydı oluşturur.

    İstek gövdesi:
        {"isim": "Ayşe", "telefon": "0555 111 22 33", "mesaj": "Pasta talebi"}

    Yanıtlar:
        201: {"basari": true, "mesaj": "...", "lead_id": 1}
        400: Zorunlu alan eksik veya telefon biçimi geçersiz.
    """
    veri = _govde_al()
    isim = _metin(veri, "isim", ISIM_MAX)
    telefon = _metin(veri, "telefon", TELEFON_MAX)
    mesaj = _metin(veri, "mesaj", MESAJ_MAX)

    zorunlu = (("isim", isim), ("telefon", telefon))
    eksikler = [alan for alan, deger in zorunlu if not deger]
    if eksikler:
        return _hata(
            "Zorunlu alanlar eksik: {}.".format(", ".join(eksikler)), 400
        )

    if not TELEFON_DESENI.match(telefon):
        return _hata("Telefon numarası biçimi geçersiz.", 400)

    try:
        lead_id = database.lead_ekle(isim, telefon, mesaj or None)
    except Exception:  # noqa: BLE001 - veritabanı detayı sızdırılmamalı
        current_app.logger.exception("Lead kaydı oluşturulamadı.")
        return _hata("Kayıt oluşturulamadı. Lütfen tekrar deneyin.", 500)

    return (
        jsonify(
            {
                "basari": True,
                "mesaj": "Talebiniz alındı, ekibimiz en kısa sürede dönecek.",
                "lead_id": lead_id,
            }
        ),
        201,
    )


@api_bp.route("/leads", methods=["GET"])
def lead_listele():
    """Kayıtlı tüm müşteri adaylarını en yeniden en eskiye listeler.

    Yanıtlar:
        200: {"basari": true, "data": [...], "toplam": 3}
    """
    try:
        leadler = database.tum_leadler()
    except Exception:  # noqa: BLE001
        current_app.logger.exception("Lead listesi okunamadı.")
        return _hata("Kayıtlar getirilemedi.", 500)

    return (
        jsonify({"basari": True, "data": leadler, "toplam": len(leadler)}),
        200,
    )
