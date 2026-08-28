"""Veritabanı katmanı (Data Access Layer).

Separation of Concerns: Uygulamadaki TÜM SQL sorguları yalnızca bu modülde
bulunur. Rotalar (`app/routes.py`) veya servisler (`services/*.py`) asla ham
SQL çalıştırmaz; yalnızca burada tanımlı fonksiyonları çağırır.

Güvenlik: Tüm sorgular parametreli placeholder kullanır. Kullanıcıdan gelen
veriler hiçbir zaman string birleştirme ile sorguya gömülmez; bu sayede SQL
Injection saldırıları engellenir.

Arka uç seçimi: `DATABASE_URL` tanımlıysa PostgreSQL, tanımlı değilse yerel
SQLite kullanılır. Dışarıya açılan fonksiyon imzaları ve dönüş biçimleri her
iki arka uçta da aynıdır; çağıran katmanlar farkı görmez.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from flask import current_app, has_app_context

from config import Config

# Veritabanı dosyası proje kök dizininde tutulur (bu dosya `app/` içindedir).
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# `leads` tablosunu oluşturan DDL'ler. Yalnızca tablo yoksa çalışır.
# SQLite: AUTOINCREMENT, PostgreSQL: SERIAL. Kolon adları ve `tarih`
# varsayılanı iki arka uçta da birebir aynıdır.
_CREATE_LEADS_TABLE_SQLITE = """
CREATE TABLE IF NOT EXISTS leads (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    isim     TEXT NOT NULL,
    telefon  TEXT NOT NULL,
    mesaj    TEXT,
    tarih    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

_CREATE_LEADS_TABLE_POSTGRES = """
CREATE TABLE IF NOT EXISTS leads (
    id       SERIAL PRIMARY KEY,
    isim     TEXT NOT NULL,
    telefon  TEXT NOT NULL,
    mesaj    TEXT,
    tarih    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


def _ayar(anahtar):
    """Aktif yapılandırmadan tek bir ayarı okur.

    Uygulama bağlamı varsa `app.config` tercih edilir; yoksa (örneğin CLI
    betikleri veya testler) doğrudan `Config` sınıfına düşülür.

    Args:
        anahtar (str): Okunacak yapılandırma anahtarı.

    Returns:
        Any: Ayarın değeri.
    """
    varsayilan = getattr(Config, anahtar)
    if has_app_context():
        return current_app.config.get(anahtar, varsayilan)
    return varsayilan


def _postgres_mi():
    """Aktif arka ucun PostgreSQL olup olmadığını söyler.

    Returns:
        bool: `DATABASE_URL` doluysa True, aksi halde False (SQLite).
    """
    return bool(_ayar("DATABASE_URL"))


def _sorgu(sablon):
    """`?` yer tutucularını aktif sürücünün beklediği biçime çevirir.

    SQLite `?`, psycopg ise `%s` bekler. Sorgular tek bir biçimde yazılıp
    burada uyarlanır; parametreler her koşulda sürücüye ayrı geçirilir.

    Args:
        sablon (str): `?` yer tutucusuyla yazılmış SQL.

    Returns:
        str: Aktif arka uca uygun SQL.
    """
    return sablon.replace("?", "%s") if _postgres_mi() else sablon


def _satir_sozluk(satir):
    """Sürücüden gelen satırı JSON'a hazır sözlüğe çevirir.

    psycopg `tarih` alanını `datetime` olarak döndürür; SQLite ise metin
    verir. API sözleşmesi bozulmasın diye iki arka uçta da aynı metin
    biçimi ("YYYY-AA-GG SS:DD:SS") üretilir.

    Args:
        satir (Mapping): Sürücüden gelen tek satır.

    Returns:
        dict: Serileştirmeye hazır kayıt.
    """
    kayit = dict(satir)
    tarih = kayit.get("tarih")
    if isinstance(tarih, datetime):
        kayit["tarih"] = tarih.strftime("%Y-%m-%d %H:%M:%S")
    return kayit


def _veritabani_yolu():
    """SQLite veritabanı dosyasının tam yolunu üretir.

    Yalnızca SQLite arka ucunda anlamlıdır.
    """
    db_name = _ayar("DATABASE_NAME")

    # Mutlak yol verildiyse olduğu gibi kullan, aksi halde kök dizine bağla.
    if os.path.isabs(db_name):
        return db_name
    return os.path.join(BASE_DIR, db_name)


def get_db():
    """Aktif arka uç için yeni bir bağlantı açar.

    Her iki sürücü de satırları kolon adıyla erişilebilir biçimde döndürür
    (SQLite'ta `sqlite3.Row`, psycopg'de `dict_row`).

    psycopg yalnızca PostgreSQL seçiliyken içe aktarılır; böylece yerel
    SQLite geliştirmesi sürücü kurulu olmadan da çalışmayı sürdürür.

    Returns:
        Connection: Kullanıma hazır bağlantı nesnesi.
    """
    if _postgres_mi():
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(_ayar("DATABASE_URL"), row_factory=dict_row)

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
        postgres = _postgres_mi()
        ddl = (
            _CREATE_LEADS_TABLE_POSTGRES
            if postgres
            else _CREATE_LEADS_TABLE_SQLITE
        )
        with _baglanti() as baglanti:
            baglanti.execute(ddl)

        # Yalnızca arka uç türü günlüğe yazılır; bağlantı adresi ve kimlik
        # bilgileri hiçbir koşulda kaydedilmez.
        if postgres:
            app.logger.info("Veritabanı hazır: PostgreSQL")
        else:
            app.logger.info(
                "Veritabanı hazır: SQLite (%s)", _veritabani_yolu()
            )


def lead_ekle(isim, telefon, mesaj=None):
    """Yeni bir müşteri adayı (lead) kaydı ekler.

    Args:
        isim (str): Müşterinin adı. Zorunlu.
        telefon (str): İletişim telefonu. Zorunlu.
        mesaj (str, optional): Talep detayı / not.

    Returns:
        int: Oluşturulan kaydın birincil anahtarı (`id`).
    """
    postgres = _postgres_mi()
    temel = "INSERT INTO leads (isim, telefon, mesaj) VALUES (?, ?, ?)"
    # PostgreSQL'de `lastrowid` yoktur; yeni anahtar RETURNING ile alınır.
    sorgu = _sorgu(temel + (" RETURNING id" if postgres else ""))

    with _baglanti() as baglanti:
        imlec = baglanti.execute(sorgu, (isim, telefon, mesaj))
        if postgres:
            return imlec.fetchone()["id"]
        return imlec.lastrowid


def tum_leadler():
    """Kayıtlı tüm müşteri adaylarını en yeniden en eskiye doğru döndürür.

    Returns:
        list[dict]: JSON'a doğrudan serileştirilebilir kayıt listesi.
    """
    sorgu = _sorgu(
        "SELECT id, isim, telefon, mesaj, tarih FROM leads ORDER BY id DESC"
    )
    with _baglanti() as baglanti:
        satirlar = baglanti.execute(sorgu).fetchall()
        # Sürücü satırları JSON'a serileştirilemez; sözlüğe çeviriyoruz.
        return [_satir_sozluk(satir) for satir in satirlar]


def lead_getir(lead_id):
    """Tek bir müşteri adayı kaydını `id` ile getirir.

    Args:
        lead_id (int): Aranan kaydın birincil anahtarı.

    Returns:
        dict | None: Kayıt bulunursa sözlük, bulunamazsa None.
    """
    sorgu = _sorgu(
        "SELECT id, isim, telefon, mesaj, tarih FROM leads WHERE id = ?"
    )
    with _baglanti() as baglanti:
        satir = baglanti.execute(sorgu, (lead_id,)).fetchone()
        return _satir_sozluk(satir) if satir else None


def lead_sayisi():
    """Toplam müşteri adayı sayısını döndürür.

    Returns:
        int: Kayıt sayısı.
    """
    with _baglanti() as baglanti:
        sorgu = _sorgu("SELECT COUNT(*) AS adet FROM leads")
        return baglanti.execute(sorgu).fetchone()["adet"]
