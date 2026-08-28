"""Yapay zekâ servis katmanı.

Separation of Concerns: Groq (LLM) API ile yapılan TÜM iletişim yalnızca bu
modülde gerçekleşir. Rotalar bu servisin genel arayüzünü çağırır, HTTP
detaylarını veya istem (prompt) kurgusunu bilmez.

KVKK / gizlilik notu: Kullanıcı mesajlarının içeriği loglanmaz; yalnızca
teknik ölçümler (karakter sayısı, HTTP durum kodu) kayda geçer.
"""

import logging

import requests

from config import Config

logger = logging.getLogger(__name__)

# .env içinde hazır gelen, gerçek anahtar olmayan yer tutucu değerler.
PLACEHOLDER_ANAHTARLAR = {
    "",
    "gsk_your_groq_api_key_here",
    "your_groq_api_key_here",
    "none",
}

# Sohbet geçmişinde kabul edilen roller. Beklenmeyen roller (örn. "system")
# istem enjeksiyonunu önlemek amacıyla filtrelenir.
IZINLI_ROLLER = {"user", "assistant"}


class AIServiceError(Exception):
    """AI sağlayıcısına erişilemediğinde veya yanıt geçersizse fırlatılır."""


class AIService:
    """Groq sohbet tamamlama API'si için ince bir sarmalayıcı."""

    def __init__(self, config=Config):
        """Servisi verilen yapılandırma ile başlatır.

        Args:
            config: `Config` sınıfı veya aynı alanlara sahip bir nesne.
        """
        self.config = config

    # ------------------------------------------------------------------
    # Yardımcı (private) metotlar
    # ------------------------------------------------------------------
    def _demo_modu_mu(self):
        """Gerçek bir API anahtarı tanımlı değilse True döner."""
        anahtar = (self.config.GROQ_API_KEY or "").strip()
        return anahtar.lower() in PLACEHOLDER_ANAHTARLAR

    def _gecmisi_temizle(self, gecmis):
        """Gelen sohbet geçmişini doğrular, filtreler ve kısaltır.

        Yalnızca `user` / `assistant` rollerine sahip, metin içeriği dolu
        kayıtlar korunur ve son `AI_MAX_HISTORY` mesajla sınırlandırılır.

        Args:
            gecmis (list | None): İstemciden gelen ham geçmiş listesi.

        Returns:
            list[dict]: Groq API biçiminde temizlenmiş mesaj listesi.
        """
        if not gecmis or not isinstance(gecmis, list):
            return []

        limit = max(0, int(self.config.AI_MAX_HISTORY))
        if limit == 0:
            return []

        temiz = []
        for kayit in gecmis:
            if not isinstance(kayit, dict):
                continue

            rol = str(kayit.get("role", "")).strip().lower()
            icerik = kayit.get("content")

            if rol not in IZINLI_ROLLER or not isinstance(icerik, str):
                continue

            icerik = icerik.strip()
            if not icerik:
                continue

            sinir = self.config.MAX_MESSAGE_LENGTH
            temiz.append({"role": rol, "content": icerik[:sinir]})

        # Yalnızca en güncel mesajları taşı (token maliyeti kontrolü).
        return temiz[-limit:]

    def _mesajlari_hazirla(self, mesaj, gecmis):
        """Sistem istemi + geçmiş + güncel soruyu tek bir listede birleştirir.

        Args:
            mesaj (str): Kullanıcının son mesajı.
            gecmis (list | None): Önceki konuşma turları.

        Returns:
            list[dict]: Groq `messages` alanına gönderilecek yapı.
        """
        mesajlar = [
            {"role": "system", "content": self.config.BUSINESS_CONTEXT}
        ]
        mesajlar.extend(self._gecmisi_temizle(gecmis))
        mesajlar.append({"role": "user", "content": mesaj})
        return mesajlar

    # ------------------------------------------------------------------
    # Genel arayüz
    # ------------------------------------------------------------------
    def yanit_uret(self, mesaj, gecmis=None):
        """Kullanıcı mesajına asistan yanıtı üretir.

        Args:
            mesaj (str): Kullanıcının sorusu. Boş olmamalıdır.
            gecmis (list, optional): `[{"role": "user", "content": "..."}]`
                biçiminde önceki konuşma turları.

        Returns:
            str: Asistanın yanıtı. Anahtar yoksa güvenli demo mesajı.

        Raises:
            AIServiceError: Ağ hatası, zaman aşımı veya geçersiz API yanıtı.
        """
        mesaj = (mesaj or "").strip()
        if not mesaj:
            raise AIServiceError("Boş mesaj ile yanıt üretilemez.")

        # Güvenli Demo Modu: anahtar yoksa servis çökmez, kibarca yönlendirir.
        if self._demo_modu_mu():
            logger.warning(
                "GROQ_API_KEY tanımlı değil; demo modu yanıtı döndürülüyor."
            )
            return self.config.DEMO_MODE_MESSAGE

        govde = {
            "model": self.config.GROQ_MODEL,
            "messages": self._mesajlari_hazirla(mesaj, gecmis),
            "temperature": self.config.AI_TEMPERATURE,
            # Groq `max_tokens` alanını `max_completion_tokens` lehine
            # kullanımdan kaldırdı; akıl yürütme modelleri için gerekli ad.
            "max_completion_tokens": self.config.AI_MAX_TOKENS,
            # Akıl yürütme metni yanıtta taşınmaz ve ücretlendirilmez.
            "include_reasoning": False,
            "reasoning_effort": "low",
        }
        basliklar = {
            "Authorization": f"Bearer {self.config.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            cevap = requests.post(
                self.config.GROQ_API_URL,
                json=govde,
                headers=basliklar,
                timeout=self.config.AI_TIMEOUT,
            )
            cevap.raise_for_status()
            veri = cevap.json()
        except requests.exceptions.Timeout as hata:
            logger.error("Groq API zaman aşımı: %s", hata)
            raise AIServiceError("AI servisi zaman aşımına uğradı.") from hata
        except requests.exceptions.HTTPError as hata:
            # Yanıt gövdesi istemciye sızdırılmaz, yalnızca sunucuya loglanır.
            yanit = hata.response
            durum = yanit.status_code if yanit is not None else "bilinmiyor"
            logger.error("Groq API HTTP hatası (durum=%s)", durum)
            raise AIServiceError(
                "AI servisi geçici olarak yanıt vermiyor."
            ) from hata
        except requests.exceptions.RequestException as hata:
            logger.error("Groq API bağlantı hatası: %s", type(hata).__name__)
            raise AIServiceError("AI servisine bağlanılamadı.") from hata
        except ValueError as hata:
            logger.error("Groq API geçersiz JSON döndürdü.")
            raise AIServiceError(
                "AI servisinden geçersiz yanıt alındı."
            ) from hata

        return self._icerigi_cikar(veri)

    @staticmethod
    def _icerigi_cikar(veri):
        """API yanıtından asistan metnini güvenli biçimde çıkarır.

        Args:
            veri (dict): Groq API'sinin JSON yanıtı.

        Returns:
            str: Asistan mesajının metin içeriği.

        Raises:
            AIServiceError: Beklenen alanlar yanıt içinde bulunamazsa.
        """
        try:
            icerik = veri["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as hata:
            logger.error("Groq API yanıtı beklenen yapıda değil.")
            raise AIServiceError("AI yanıtı işlenemedi.") from hata

        icerik = (icerik or "").strip()
        if not icerik:
            raise AIServiceError("AI servisi boş yanıt döndürdü.")
        return icerik


# Uygulama genelinde paylaşılan tek örnek (singleton).
ai_service = AIService()
