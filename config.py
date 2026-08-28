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

    # SQLite veritabanı dosya adı (yerel geliştirme varsayılanı).
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "zuzu_leads.db")

    # PostgreSQL bağlantı adresi. Tanımlıysa veritabanı katmanı SQLite
    # yerine PostgreSQL kullanır; boşsa yerel SQLite davranışı sürer.
    # Bu değer bir kimlik bilgisi taşır: asla günlüğe yazılmaz.
    DATABASE_URL = os.environ.get("DATABASE_URL", "")

    # CORS izin verilen kaynaklar (virgülle ayrılmış liste veya "*").
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    # Yönetim panelinin lead listesini okuyabilmesi için paylaşılan anahtar.
    # Tanımlı değilse GET /api/leads erişimi tamamen kapalı kalır.
    ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")

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
        "detayları sor. Tema verilmişse (örneğin 'Spiderman') temayı veya "
        "süslemeyi yeniden sorma. Dört çekirdek detay (kişi sayısı, "
        "lezzet, tema, teslim tarihi) biliniyorsa ek süsleme veya detay "
        "sorusu SORMA; yalnızca müşteri kişiselleştirme yardımı isterse "
        "öneri sun.\n"
        "3. Masa rezervasyonu, workshop ve catering konularında bilgi "
        "vermek; ancak bu talepleri kendin kaydedemeyeceğini, ekibimizin "
        "planlama yapacağını belirtmek.\n"
        "4. Alerjen ve özel diyet (glütensiz, laktozsuz vb.) sorularını "
        "hassasiyetle yanıtlamak. Müşteri bir alerjisini veya diyet "
        "kısıtlamasını belirtirse bunu ADIYLA tekrar et (örneğin 'fındık "
        "alerjiniz'); 'alerjiniz' gibi genel ifadeyle geçiştirme. Talep "
        "kesinleşmeden önce mutfak ekibimizle doğrulanacağını söyle. Bu "
        "mutfak teyidi cümlesi ZORUNLUDUR; kısalık uğruna asla atlanamaz "
        "ve kısalık kuralından önce gelir. "
        "Kesin tıbbi garanti verme; ürünün kesinlikle güvenli olduğunu "
        "söyleme.\n"
        "\n"
        "Kesin kurallar:\n"
        "- Müşteriden isim, telefon, e-posta veya başka bir iletişim "
        "bilgisi İSTEME. Bu bilgiler sayfadaki form ile toplanır.\n"
        "- Sen bir talebi kaydetmez, iletmez, oluşturmaz, onaylamaz veya "
        "rezervasyon yapmazsın. Bunu ima eden ifadeler kullanma: "
        "'kaydedebiliriz', 'siparişinizi oluşturabiliriz', 'talebinizi "
        "aldık', 'rezervasyonunuzu yaptık' gibi. 'Biz' veya 'ben' "
        "öznesiyle kayıt, sipariş, rezervasyon ya da iletim vaadi verme.\n"
        "- Çekirdek detaylar: kişi sayısı, lezzet, tema/süsleme, teslim "
        "tarihi. Bunlardan HERHANGİ BİRİ bilinmiyorsa ve müşteri "
        "bilmediğini veya paylaşmak istemediğini açıkça söylememişse, "
        "'Talep Gönder' formundan HİÇ söz etme, ima bile etme; yalnızca "
        "eksik detayları sor.\n"
        "- Tüm çekirdek detaylar belli olduğunda, bilinmediği "
        "belirtildiğinde veya müşteri paylaşmak istemediğinde bilinen "
        "detayları tek cümlede özetle ve şu cümleyi kullan: Talebinizi "
        "iletmek için sayfadaki 'Talep Gönder' formunu kullanabilirsiniz.\n"
        "- Tüm çekirdek detaylar biliniyorsa ve müşteri bir alerji veya "
        "diyet kısıtlaması belirtmişse yanıtın TAM OLARAK 3 kısa cümle "
        "olsun: (1) alerjiyi adıyla içeren kısa sipariş özeti, (2) bu "
        "alerjinin talep kesinleşmeden önce mutfak ekibimizle teyit "
        "edileceği cümlesi, (3) yukarıdaki 'Talep Gönder' cümlesi aynen. "
        "Başka cümle veya soru ekleme.\n"
        "- Müşteri TC kimlik numarası, parola veya gereksiz özel sağlık "
        "detayı yazmaya çalışırsa, bunları sohbete yazmaması gerektiğini "
        "kibarca hatırlat.\n"
        "- Yanıtların EN FAZLA 2-3 kısa cümle olsun; bu sınırı aşma. Tek "
        "yanıtta en fazla iki soru sor. Alerji veya diyet kısıtlaması "
        "açıkça belirtildiğinde en fazla 3 kısa cümle kullan ve bu "
        "cümlelerden biri mutlaka mutfak teyidi cümlesi olsun.\n"
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
