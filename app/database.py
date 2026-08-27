"""Veritabanı katmanı (Data Access Layer).

Separation of Concerns: Uygulamadaki TÜM SQL sorguları yalnızca bu modülde
bulunur. Rotalar (`app/routes.py`) veya servisler (`services/*.py`) asla ham
SQL çalıştırmaz; yalnızca burada tanımlı fonksiyonları çağırır.

Güvenlik: Tüm sorgular parametreli placeholder (`?`) kullanır. Kullanıcıdan
gelen veriler hiçbir zaman string birleştirme ile sorguya gömülmez; bu sayede
SQL Injection saldırıları engellenir.
"""

import os
import sqlite3
from contextlib import contextmanager

from flask import current_app, has_app_context

from config import Config

# Veritabanı dosyası proje kök dizininde tutulur (bu dosya `app/` içindedir).
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# `leads` tablosunu oluşturan DDL. Yalnızca tablo yoksa çalışır.
_CREATE_LEADS_TABLE = """
CREATE TABLE IF NOT EXISTS leads (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    isim     TEXT NOT NULL,
    telefon  TEXT NOT NULL,
    mesaj    TEXT,
    tarih    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


def _veritabani_yolu():
    """Aktif yapılandırmadan veritabanı dosyasının tam yolunu üretir.

    Uygulama bağlamı varsa `app.config` tercih edilir; yoksa (örneğin CLI
    betikleri veya testler) doğrudan `Config` sınıfına düşülür.
    """
    if has_app_context():
        db_name = current_app.config.get("DATABASE_NAME", Config.DATABASE_NAME)
    else:
        db_name = Config.DATABASE_NAME

    # Mutlak yol verildiyse olduğu gibi kullan, aksi halde kök dizine bağla.
    if os.path.isabs(db_name):
        return db_name
    return os.path.join(BASE_DIR, db_name)


def get_db():
    """Yeni bir SQLite bağlantısı açar ve satırları sözlük gibi sunar.

    `sqlite3.Row` factory sayesinde sonuçlara kolon adıyla erişilebilir
    (örn. `satir["isim"]`).

    Returns:
        sqlite3.Connection: Kullanıma hazır bağlantı nesnesi.
    """
    baglanti = sqlite3.connect(_veritabani_yolu())
    baglanti.row_factory = sqlite3.Row
    # Yabancı anahtar kısıtlarını etkinleştir (SQLite'ta varsayılan kapalıdır).
    baglanti.execute("PRAGMA foreign_keys = ON")
    return baglanti


@contextmanager
def _baglanti():
    """Bağlantıyı otomatik commit/rollback ve kapatma ile yöneten yardımcı.

    Hata durumunda değişiklikler geri alınır, her koşulda bağlantı kapatılır.
    """
    baglanti = get_db()
    try:
        yield baglanti
        baglanti.commit()
    except Exception:
        baglanti.rollback()
        raise
    finally:
        baglanti.close()


def init_db(app):
    """Veritabanı şemasını hazırlar (tablo yoksa oluşturur).

    Uygulama fabrikası (`create_app`) tarafından bir kez çağrılır.

    Args:
        app (Flask): Yapılandırması yüklenmiş Flask uygulaması.
    """
    with app.app_context():
        with _baglanti() as baglanti:
            baglanti.execute(_CREATE_LEADS_TABLE)
        app.logger.info("Veritabanı hazır: %s", _veritabani_yolu())


def lead_ekle(isim, telefon, mesaj=None):
    """Yeni bir müşteri adayı (lead) kaydı ekler.

    Args:
        isim (str): Müşterinin adı. Zorunlu.
        telefon (str): İletişim telefonu. Zorunlu.
        mesaj (str, optional): Talep detayı / not.

    Returns:
        int: Oluşturulan kaydın birincil anahtarı (`id`).
    """
    sorgu = "INSERT INTO leads (isim, telefon, mesaj) VALUES (?, ?, ?)"
    with _baglanti() as baglanti:
        imlec = baglanti.execute(sorgu, (isim, telefon, mesaj))
        return imlec.lastrowid


def tum_leadler():
    """Kayıtlı tüm müşteri adaylarını en yeniden en eskiye doğru döndürür.

    Returns:
        list[dict]: JSON'a doğrudan serileştirilebilir kayıt listesi.
    """
    sorgu = (
        "SELECT id, isim, telefon, mesaj, tarih FROM leads ORDER BY id DESC"
    )
    with _baglanti() as baglanti:
        satirlar = baglanti.execute(sorgu).fetchall()
        # sqlite3.Row JSON'a serileştirilemez; sözlüğe çeviriyoruz.
        return [dict(satir) for satir in satirlar]


def lead_getir(lead_id):
    """Tek bir müşteri adayı kaydını `id` ile getirir.

    Args:
        lead_id (int): Aranan kaydın birincil anahtarı.

    Returns:
        dict | None: Kayıt bulunursa sözlük, bulunamazsa None.
    """
    sorgu = "SELECT id, isim, telefon, mesaj, tarih FROM leads WHERE id = ?"
    with _baglanti() as baglanti:
        satir = baglanti.execute(sorgu, (lead_id,)).fetchone()
        return dict(satir) if satir else None


def lead_sayisi():
    """Toplam müşteri adayı sayısını döndürür.

    Returns:
        int: Kayıt sayısı.
    """
    with _baglanti() as baglanti:
        sorgu = "SELECT COUNT(*) AS adet FROM leads"
        return baglanti.execute(sorgu).fetchone()["adet"]
