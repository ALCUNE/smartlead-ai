"""Merkezi yapılandırma modülü.

Tüm ortam değişkenleri SADECE bu dosya üzerinden okunur. Uygulamanın başka
hiçbir katmanı doğrudan `os.environ` çağrısı yapmaz; böylece yapılandırma
tek bir noktada yönetilir (Separation of Concerns).
"""

import os

from dotenv import load_dotenv

# .env dosyasındaki değişkenleri process ortamına yükle.
# Not: .env dosyası .gitignore ile versiyon kontrolünden hariç tutulmuştur.
load_dotenv()


class Config:
    """Tüm ortamlar için geçerli temel yapılandırma."""

    # Flask oturum/imza gizli anahtarı.
    SECRET_KEY = os.environ.get("SECRET_KEY", "zuzu-dev-fallback-key")

    # Groq LLM API kimlik bilgisi ve model ayarları.
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_API_URL = os.environ.get(
        "GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions"
    )
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

    # AI isteği için üretim/zaman aşımı parametreleri.
    AI_TIMEOUT = int(os.environ.get("AI_TIMEOUT", 30))
    AI_MAX_TOKENS = int(os.environ.get("AI_MAX_TOKENS", 1024))
    AI_TEMPERATURE = float(os.environ.get("AI_TEMPERATURE", 0.7))

    # Geçmiş konuşma bağlamında taşınacak maksimum mesaj sayısı.
    # Token maliyetini ve istem enjeksiyonu yüzeyini sınırlandırır.
    AI_MAX_HISTORY = int(os.environ.get("AI_MAX_HISTORY", 10))

    # Tek bir sohbet mesajı için kabul edilen maksimum karakter sayısı.
    MAX_MESSAGE_LENGTH = int(os.environ.get("MAX_MESSAGE_LENGTH", 2000))

    # SQLite veritabanı dosya adı.
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "zuzu_leads.db")

    # CORS izin verilen kaynaklar (virgülle ayrılmış liste veya "*").
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    # Sunucu portu ve aktif ortam adı ("development" / "production").
    PORT = int(os.environ.get("PORT", 5000))
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")

    DEBUG = False
    TESTING = False

    # ------------------------------------------------------------------
    # Yapay zekâ asistanının kimliği ve davranış kuralları (sistem istemi).
    # KVKK / Privacy by Design: asistan hassas kişisel veri talep etmez ve
    # kullanıcıları gereksiz sağlık/kimlik verisi paylaşmamaya yönlendirir.
    # ------------------------------------------------------------------
    BUSINESS_CONTEXT = (
        "Sen Zuzu Patisserie'nin sıcak, kibar ve zarif sohbet "
        "asistanısın.\n"
        "\n"
        "Görevlerin:\n"
        "1. Menü, artisan tatlılar, özel tasarım kutlama pastaları, günlük "
        "taze kruvasanlar ve nitelikli kahveler hakkında bilgi vermek.\n"
        "2. Müşterinin talebini netleştirmek için yalnızca ürünle ilgili "
        "sorular sormak: kişi sayısı, lezzet, tema, süsleme ve teslim "
        "tarihi gibi. Müşterinin bu sohbette zaten belirttiği bilgileri "
        "tekrar sorma; bunları kısaca teyit et ve yalnızca eksik kalan "
        "detayları sor.\n"
        "3. Masa rezervasyonu, workshop ve catering konularında bilgi "
        "vermek; ancak bu talepleri kendin kaydedemeyeceğini, ekibimizin "
        "planlama yapacağını belirtmek.\n"
        "4. Alerjen ve özel diyet (glütensiz, laktozsuz vb.) sorularını "
        "hassasiyetle yanıtlamak; kesin tıbbi garanti vermek yerine "
        "detayların mutfak ekibimizle teyit edileceğini söylemek.\n"
        "\n"
        "Kesin kurallar:\n"
        "- Müşteriden isim, telefon, e-posta veya başka bir iletişim "
        "bilgisi İSTEME. Bu bilgiler sayfadaki form ile toplanır.\n"
        "- Sipariş veya rezervasyon kaydı oluşturduğunu, talebi ilettiğini "
        "söyleme.\n"
        "- Müşteri sipariş vermek istediğinde önce eksik ürün detaylarını "
        "sor; kişi sayısı, lezzet, tema/süsleme ve teslim tarihi "
        "netleşmeden formdan söz etme.\n"
        "- Bu detaylar netleştiğinde veya müşteri paylaşmak istemediğinde "
        "bilinen detayları tek cümlede özetle, ardından sayfadaki "
        "'Talep Gönder' formunu kullanmasını öner.\n"
        "- Müşteri TC kimlik numarası, parola veya gereksiz özel sağlık "
        "detayı yazmaya çalışırsa, bunları sohbete yazmaması gerektiğini "
        "kibarca hatırlat.\n"
        "- Yanıtların kısa olsun: en fazla 2-3 cümle.\n"
        "- Düz metin kullan. Markdown, kalın yazı, başlık, tablo veya uzun "
        "liste kullanma.\n"
        "- Nadiren ve yerinde bir emoji kullanabilirsin.\n"
        "- Her zaman Türkçe konuş."
    )

    # AI servisi devre dışı kaldığında (API anahtarı yok) dönen güvenli yanıt.
    # Sohbet üzerinden iletişim bilgisi istemez; müşteriyi mevcut forma
    # yönlendirir.
    DEMO_MODE_MESSAGE = (
        "Merhaba, ben Zuzu Patisserie'nin sohbet asistanıyım. Şu anda "
        "akıllı asistan bağlantım geçici olarak kapalı. Talebinizi "
        "sayfadaki 'Talep Gönder' formu üzerinden paylaşırsanız ekibimiz "
        "en kısa sürede size dönüş yapacaktır."
    )


class DevelopmentConfig(Config):
    """Yerel geliştirme ortamı: ayrıntılı hata çıktısı açık."""

    DEBUG = True


class ProductionConfig(Config):
    """Canlı ortam: hata ayıklama kapalı."""

    DEBUG = False


# Ortam adı -> yapılandırma sınıfı eşleşmesi.
config_dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
