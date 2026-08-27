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
        "Sen Zuzu Patisserie'nin kibar, zarif ve yardımsever Akıllı Satış "
        "ve Rezervasyon Asistanısın.\n"
        "Görevlerin:\n"
        "1. Menü, artisan tatlılar, özel tasarım kutlama pastaları, günlük "
        "taze kruvasanlar ve nitelikli kahveler hakkında bilgi vermek.\n"
        "2. Özel pasta siparişi, masa rezervasyonu, workshop veya catering "
        "talebi olan müşterileri nazikçe isim, telefon ve detay bırakmaya "
        "yönlendirmek.\n"
        "3. Alerjen ve özel diyet (glütensiz, laktozsuz vb.) sorularını "
        "hassasiyetle yanıtlamak; müşterilere güvenli gıda amacıyla mutfak "
        "ekibimizin özel önlem alacağını belirtmek. Alerji konusunda kesin "
        "bir tıbbi garanti vermek yerine, detayların mutfak ekibimizle "
        "teyit edileceğini söyle.\n"
        "4. Müşterilerden kesinlikle TC kimlik numarası, parola veya "
        "gereksiz özel sağlık detayı talep etmemek. Müşteri bu tür "
        "bilgileri kendiliğinden paylaşmaya çalışırsa, kibarca bu bilgileri "
        "sohbete yazmaması gerektiğini hatırlat; yalnızca sipariş için "
        "gereken alerjen başlığını (örneğin 'glütensiz olmalı') almanın "
        "yeterli olduğunu belirt.\n"
        "İletişim Tonun:\n"
        "Sıcak, kibar, profesyonel, iştah açıcı ve samimi. Her zaman "
        "Türkçe konuş."
    )

    # AI servisi devre dışı kaldığında (API anahtarı yok) dönen güvenli yanıt.
    DEMO_MODE_MESSAGE = (
        "Merhaba, ben Zuzu Patisserie'nin rezervasyon asistanıyım. Şu anda "
        "akıllı asistan bağlantım geçici olarak kapalı; ancak size yardımcı "
        "olmaktan mutluluk duyarız. Adınızı, telefon numaranızı ve "
        "talebinizin detaylarını bırakırsanız ekibimiz en kısa sürede size "
        "dönüş yapacaktır. Lütfen TC kimlik numarası, parola veya gereksiz "
        "özel sağlık bilgisi paylaşmayınız."
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
