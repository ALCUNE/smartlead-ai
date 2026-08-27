"""Uygulama fabrikası (Application Factory).

Flask uygulamasını oluşturur, yapılandırmayı yükler, eklentileri başlatır ve
Blueprint'leri kaydeder. Böylece uygulama test/geliştirme/canlı ortamlar için
farklı yapılandırmalarla birden fazla kez üretilebilir.
"""

import logging

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from config import Config, config_dict


def _cors_kaynaklari(deger):
    """CORS yapılandırma değerini flask-cors'un beklediği biçime çevirir.

    Args:
        deger (str): "*" veya virgülle ayrılmış origin listesi.

    Returns:
        str | list[str]: Tek joker karakter ya da origin listesi.
    """
    if not deger or deger.strip() == "*":
        return "*"
    return [parca.strip() for parca in deger.split(",") if parca.strip()]


def _hata_yoneticileri_kaydet(app):
    """Tüm hataları temiz JSON olarak döndüren yöneticileri bağlar.

    Gizlilik gereği istemciye traceback veya iç dosya yolları gönderilmez.
    """

    @app.errorhandler(400)
    def _kotu_istek(hata):  # noqa: ANN001 - Flask imzası
        return jsonify({"basari": False, "hata": "Geçersiz istek."}), 400

    @app.errorhandler(404)
    def _bulunamadi(hata):  # noqa: ANN001
        return jsonify({"basari": False, "hata": "Kaynak bulunamadı."}), 404

    @app.errorhandler(405)
    def _yontem_yasak(hata):  # noqa: ANN001
        return (
            jsonify({"basari": False, "hata": "Bu yöntem desteklenmiyor."}),
            405,
        )

    @app.errorhandler(500)
    def _sunucu_hatasi(hata):  # noqa: ANN001
        app.logger.error("Sunucu hatası: %s", hata)
        return jsonify({"basari": False, "hata": "Sunucu hatası oluştu."}), 500

    @app.errorhandler(Exception)
    def _beklenmeyen(hata):  # noqa: ANN001
        # HTTP kaynaklı hatalar kendi durum kodu ve açıklamasıyla döner.
        if isinstance(hata, HTTPException):
            return (
                jsonify({"basari": False, "hata": hata.description}),
                hata.code,
            )

        # Diğer her şeyde ayrıntılar yalnızca sunucu günlüğüne yazılır.
        app.logger.exception("Yakalanmayan istisna: %s", type(hata).__name__)
        return (
            jsonify({"basari": False, "hata": "Beklenmeyen bir hata oluştu."}),
            500,
        )


def create_app(config_name=None):
    """Yapılandırılmış bir Flask uygulaması üretir.

    Args:
        config_name (str, optional): "development" veya "production".
            Verilmezse `.env` içindeki `FLASK_ENV` değeri kullanılır.

    Returns:
        Flask: Kullanıma hazır uygulama örneği.
    """
    app = Flask(__name__)

    # 1) Yapılandırma
    ortam = config_name or Config.FLASK_ENV
    app.config.from_object(config_dict.get(ortam, config_dict["default"]))

    # Türkçe karakterlerin JSON yanıtlarında okunabilir kalması için.
    app.json.ensure_ascii = False

    logging.basicConfig(
        level=logging.DEBUG if app.config["DEBUG"] else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # 2) Eklentiler
    izinli_kaynaklar = _cors_kaynaklari(app.config["CORS_ORIGINS"])
    CORS(app, resources={r"/api/*": {"origins": izinli_kaynaklar}})

    # 3) Veritabanı şeması (döngüsel import'u önlemek için yerel import)
    from app.database import init_db

    init_db(app)

    # 4) Blueprint kaydı
    from app.routes import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    # 5) Hata yöneticileri
    _hata_yoneticileri_kaydet(app)

    @app.route("/health", methods=["GET"])
    def health():
        """Yük dengeleyici / izleme sistemleri için basit sağlık kontrolü."""
        return jsonify(
            {"durum": "aktif", "servis": "Zuzu Patisserie SmartLead AI API"}
        ), 200

    app.logger.info("SmartLead AI başlatıldı (ortam=%s)", ortam)
    return app
