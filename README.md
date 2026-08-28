# SmartLead AI — Zuzu Patisserie

SmartLead AI, butik bir Fransız artisan pastane ve pasta stüdyosu olan
**Zuzu Patisserie** için geliştirilmiş, modüler bir Flask backend projesidir.

Proje iki temel akışı birlikte yürütür:

- **Ziyaretçiler**, site üzerindeki sohbet alanından yapay zekâ asistanına
  soru sorabilir; menü, özel tasarım pastalar, alerjen ve teslimat gibi
  konularda bilgi alabilir. Talep detayları netleştikten sonra ziyaretçi,
  sayfadaki "Talep Gönder" formu ile talebini iletir.
- **Yetkili personel**, Wix üzerindeki yönetim panelinden gönderilmiş
  talepleri (lead kayıtlarını) görüntüleyebilir. Bu liste yalnızca yönetim
  anahtarı ile erişilebilen korumalı bir uç nokta üzerinden sunulur.

Sohbet asistanı bilinçli olarak iletişim bilgisi toplamaz; isim ve telefon
gibi veriler yalnızca sayfadaki form aracılığıyla alınır. Böylece sohbet
akışı ile veri toplama akışı birbirinden ayrılmış olur.

## Özellikler

- **Yapay zekâ sohbet asistanı:** Groq API üzerinden çalışan, Zuzu
  Patisserie bağlamına göre yapılandırılmış Türkçe asistan.
- **Çok turlu sohbet geçmişi:** İstemciden gelen `gecmis` alanı sayesinde
  asistan önceki mesajları hatırlar; geçmiş `AI_MAX_HISTORY` kadar mesajla
  sınırlandırılır ve yalnızca `user` / `assistant` rolleri kabul edilir.
- **Talep (lead) kaydı:** Ziyaretçi formundan gelen isim, telefon ve mesaj
  bilgileri doğrulanarak veritabanına yazılır.
- **Korumalı talep listesi:** Yönetim paneli için `X-Admin-Key` başlığı ile
  korunan liste uç noktası.
- **Render üzerinde PostgreSQL kalıcılığı:** `DATABASE_URL` tanımlıysa tüm
  kayıtlar PostgreSQL üzerinde tutulur.
- **Yerel geliştirmede SQLite:** `DATABASE_URL` tanımlı değilse uygulama
  otomatik olarak yerel SQLite dosyasına düşer.
- **Wix / Velo entegrasyonu:** Müşteri sayfası ve yönetim paneli bu backend
  ile HTTP üzerinden konuşur.
- **Güvenli demo modu:** Geçerli bir `GROQ_API_KEY` tanımlı değilse servis
  hata vermek yerine kullanıcıyı forma yönlendiren sabit bir yanıt döner.

## Mimari ve Separation of Concerns

Proje, her katmanın tek bir sorumluluğu olduğu bir yapı üzerine kuruludur:

| Dosya | Sorumluluk |
| --- | --- |
| `config.py` | Tüm ortam değişkenlerinin okunduğu tek nokta. Asistanın sistem istemi (`BUSINESS_CONTEXT`) da burada tanımlıdır. |
| `app/database.py` | Veritabanı bağlantısı, şema oluşturma ve tüm SQL sorguları. |
| `services/ai_service.py` | Groq API ile yapılan tüm iletişim, istem kurgusu ve hata yönetimi. |
| `app/routes.py` | HTTP katmanı: istek doğrulama, ilgili katmana yönlendirme ve tutarlı JSON yanıtı. |
| `app/__init__.py` | Uygulama fabrikası (`create_app`): yapılandırma, CORS, veritabanı başlatma, blueprint kaydı, hata yöneticileri ve `/health`. |
| `run.py` | WSGI giriş noktası; `app` nesnesini üretir. |

Bu ayrımın iki kuralı açıktır ve kod tabanında bilinçli olarak korunur:

- **Ham SQL yalnızca `app/database.py` içinde bulunur.** Rotalar ve
  servisler asla doğrudan SQL çalıştırmaz; yalnızca bu modüldeki
  fonksiyonları çağırır.
- **Groq API çağrıları yalnızca `services/ai_service.py` içinde yapılır.**
  Rotalar servisin genel arayüzünü çağırır, HTTP detaylarını veya istem
  kurgusunu bilmez.

## Proje Yapısı

```
smartlead_ai/
├── app/
│   ├── __init__.py        # Uygulama fabrikası, CORS, hata yöneticileri, /health
│   ├── database.py        # Bağlantı yönetimi, şema ve tüm SQL sorguları
│   └── routes.py          # API rotaları: doğrulama ve yönlendirme
├── services/
│   ├── __init__.py
│   └── ai_service.py      # Groq API istemcisi ve istem yönetimi
├── config.py              # Merkezi yapılandırma (ortam değişkenleri)
├── requirements.txt       # Python bağımlılıkları
├── run.py                 # WSGI giriş noktası
├── .gitignore
└── README.md
```

`.env` dosyası ve SQLite veritabanı dosyaları `.gitignore` ile sürüm
kontrolünden hariç tutulduğu için bu ağaçta yer almaz.

## Teknolojiler

- **Python 3** ve **Flask** (uygulama fabrikası deseni)
- **flask-cors** — tarayıcı kaynak kısıtlaması
- **Groq API** — sohbet tamamlama servisi
- **openai/gpt-oss-20b** — varsayılan dil modeli (`GROQ_MODEL` ile
  değiştirilebilir)
- **SQLite** — yerel geliştirme veritabanı
- **PostgreSQL** ve **psycopg** — canlı ortam veritabanı ve sürücüsü
- **Gunicorn** — WSGI sunucusu
- **Render** — barındırma platformu
- **Wix / Velo** — müşteri arayüzü ve yönetim paneli
- **python-dotenv**, **requests** — yapılandırma ve HTTP istemcisi

## API Endpointleri

Tüm API uç noktaları `/api` ön ekiyle kayıtlıdır; `/health` ise doğrudan
kök dizinde yer alır. Yanıtlar tutarlı bir JSON sözleşmesi kullanır ve hata
durumlarında istemciye teknik detay (traceback) gönderilmez.

| Metot | Yol | Yetki | Başarılı yanıt |
| --- | --- | --- | --- |
| `GET` | `/health` | Yok | `200` |
| `POST` | `/api/sohbet` | Yok | `200` |
| `POST` | `/api/leads` | Yok (herkese açık form) | `201` |
| `GET` | `/api/leads` | `X-Admin-Key` başlığı | `200` |

### `GET /health`

Servisin ayakta olduğunu bildirir.

```json
{ "durum": "aktif", "servis": "Zuzu Patisserie SmartLead AI API" }
```

### `POST /api/sohbet`

Müşteri mesajına asistan yanıtı döndürür.

```json
{ "mesaj": "10 kişilik çikolatalı pasta yapıyor musunuz?", "gecmis": [] }
```

`gecmis` isteğe bağlıdır ve `{"role": "...", "content": "..."}` biçiminde
kayıtlardan oluşan bir liste olmalıdır. Başarılı yanıt:

```json
{ "basari": true, "cevap": "..." }
```

Durum kodları: `400` (`mesaj` boş ya da `gecmis` liste değil), `503` (yapay
zekâ servisine ulaşılamıyor), `500` (beklenmeyen hata).

### `POST /api/leads`

Yeni bir talep kaydı oluşturur. Müşteri formunun kullandığı, herkese açık
uç noktadır.

```json
{ "isim": "Ayşe Yılmaz", "telefon": "0555 111 22 33", "mesaj": "Pasta talebi" }
```

`isim` ve `telefon` zorunludur; telefon numarası yalnızca rakam, boşluk,
`+`, `-` ve parantez içerebilir ve 7-25 karakter uzunluğunda olmalıdır.
Başarılı yanıt:

```json
{ "basari": true, "mesaj": "Talebiniz alındı, ...", "lead_id": 1 }
```

Durum kodları: `201` (oluşturuldu), `400` (zorunlu alan eksik veya telefon
biçimi geçersiz), `500` (kayıt oluşturulamadı).

### `GET /api/leads`

Kayıtlı tüm talepleri en yeniden en eskiye listeler. Kişisel veri içerdiği
için yalnızca geçerli `X-Admin-Key` başlığı ile erişilebilir.

```json
{ "basari": true, "data": [ ... ], "toplam": 3 }
```

Durum kodları: `200` (başarılı), `401` (anahtar eksik veya geçersiz),
`503` (sunucuda `ADMIN_API_KEY` tanımlı değil — erişim kapalı kalır),
`500` (kayıtlar okunamadı).

## Ortam Değişkenleri

Tüm ortam değişkenleri yalnızca `config.py` üzerinden okunur. Aşağıdaki
tabloda **gizli** olarak işaretlenen değerler asla depoya, Wix sayfa koduna
veya bu dosyaya yazılmamalıdır.

| Değişken | Gizli | Amaç | Varsayılan |
| --- | --- | --- | --- |
| `SECRET_KEY` | Evet | Flask oturum/imza anahtarı | geliştirme değeri |
| `GROQ_API_KEY` | Evet | Groq API kimlik bilgisi | boş (demo modu) |
| `GROQ_API_URL` | Hayır | Groq sohbet tamamlama adresi | Groq varsayılan adresi |
| `GROQ_MODEL` | Hayır | Kullanılacak dil modeli | `openai/gpt-oss-20b` |
| `AI_TIMEOUT` | Hayır | Groq isteği zaman aşımı (saniye) | `30` |
| `AI_MAX_TOKENS` | Hayır | Yanıt için üst token sınırı | `1024` |
| `AI_TEMPERATURE` | Hayır | Yanıt çeşitliliği | `0.7` |
| `AI_MAX_HISTORY` | Hayır | Bağlamda taşınacak en fazla mesaj sayısı | `10` |
| `MAX_MESSAGE_LENGTH` | Hayır | Tek sohbet mesajı karakter sınırı | `2000` |
| `DATABASE_NAME` | Hayır | SQLite dosya adı veya mutlak yolu | `zuzu_leads.db` |
| `DATABASE_URL` | Evet | PostgreSQL bağlantı adresi | boş (SQLite kullanılır) |
| `CORS_ORIGINS` | Hayır | İzin verilen kaynaklar (`*` veya virgüllü liste) | `*` |
| `ADMIN_API_KEY` | Evet | `GET /api/leads` için yönetim anahtarı | boş (erişim kapalı) |
| `PORT` | Hayır | Yerel sunucu portu | `5000` |
| `FLASK_ENV` | Hayır | `development` veya `production` | `development` |

Değerler yerelde `.env` dosyasından, canlı ortamda ise Render ortam
değişkenlerinden okunur. **`.env` dosyası `.gitignore` ile sürüm
kontrolünden hariç tutulmuştur** ve depoya hiçbir zaman eklenmez.

## Yerel Kurulum ve Çalıştırma

```bash
# 1) Depoyu klonlayın
git clone https://github.com/ALCUNE/smartlead-ai.git
cd smartlead-ai

# 2) Sanal ortam oluşturun ve etkinleştirin
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3) Bağımlılıkları kurun
pip install -r requirements.txt

# 4) Ortam değişkenlerini tanımlayın
#    Proje kökünde bir .env dosyası oluşturup en azından
#    SECRET_KEY, GROQ_API_KEY ve ADMIN_API_KEY değerlerini girin.

# 5) Uygulamayı çalıştırın
python run.py
```

Uygulama varsayılan olarak `http://localhost:5000` adresinde çalışır.

`DATABASE_URL` tanımlı olmadığı sürece uygulama **otomatik olarak SQLite**
kullanır; yerel geliştirme için PostgreSQL kurulumu gerekmez.

`GROQ_API_KEY` tanımlı değilse sohbet uç noktası hata vermez; kullanıcıyı
forma yönlendiren sabit bir demo yanıtı döner.

## Veritabanı ve Kalıcılık

Veritabanı katmanı iki arka ucu destekler ve seçim tek bir değişkene bağlıdır:

- **`DATABASE_URL` tanımlıysa → PostgreSQL** (psycopg ile bağlanılır).
- **`DATABASE_URL` boş veya tanımsızsa → SQLite** (yerel dosya).

Her iki durumda da dışarıya açılan fonksiyon imzaları ve JSON yanıt biçimi
aynıdır; `app/routes.py` hangi arka ucun kullanıldığını bilmez.

`leads` tablosu uygulama açılışında `init_db()` tarafından otomatik olarak
oluşturulur (`CREATE TABLE IF NOT EXISTS`); ayrıca bir kurulum adımı
gerekmez. Tablo `id`, `isim`, `telefon`, `mesaj` ve `tarih` sütunlarından
oluşur.

Render üzerindeki canlı ortam şu anda **PostgreSQL** kullanmaktadır. Bu
kurulum staj/demo ortamı içindir; Render'ın ücretsiz PostgreSQL planı
kalıcı bir üretim altyapısı olarak değerlendirilmemelidir.

## Wix / Velo Entegrasyonu

- **Müşteri sayfası**, herkese açık uç noktaları doğrudan çağırır:
  sohbet alanı `POST /api/sohbet`, "Talep Gönder" formu ise
  `POST /api/leads` adresine istek gönderir.
- **Yönetim paneli**, gönderilmiş talepleri listeler ve bunun için
  `GET /api/leads` uç noktasını kullanır.
- Bu uç nokta `X-Admin-Key` başlığı ile korunduğundan, panel isteği
  **Wix backend (web module) katmanı üzerinden** yapılmalıdır. Anahtar
  **Wix Secrets Manager** içinde saklanır.
- `ADMIN_API_KEY` değeri hiçbir koşulda frontend/sayfa koduna
  yazılmamalıdır; tarayıcıya inen her değer ziyaretçiler tarafından
  görülebilir.

## Güvenlik ve KVKK Yaklaşımı

Aşağıdakiler, projede uygulanan gizlilik ve güvenlik odaklı önlemlerdir.
Bunlar bir hukuki uygunluk beyanı veya sertifikasyon değildir.

- **Parametreli SQL:** Tüm sorgular yer tutucu kullanır; kullanıcı verisi
  hiçbir zaman string birleştirme ile sorguya gömülmez.
- **Gizli bilgilerin korunması:** `.env` sürüm kontrolüne dâhil edilmez;
  anahtarlar yalnızca ortam değişkenlerinden okunur.
- **Korumalı liste uç noktası:** `GET /api/leads` yalnızca geçerli
  `X-Admin-Key` başlığıyla erişilebilir.
- **`hmac.compare_digest`:** Anahtar karşılaştırması zamanlama
  saldırılarına karşı sabit süreli yapılır. Sunucuda anahtar tanımlı
  değilse erişim açılmaz (fail-closed).
- **CORS yapılandırması:** Tarayıcı erişimi `CORS_ORIGINS` ile
  sınırlandırılabilir; kısıtlama `/api/*` yollarına uygulanır.
- **Güvenli JSON hata yanıtları:** İstemciye traceback veya iç dosya yolu
  gönderilmez; ayrıntılar yalnızca sunucu günlüğüne yazılır.
- **Veri minimizasyonu:** Sohbet mesajlarının içeriği loglanmaz. Asistan
  sohbette iletişim bilgisi istemez ve kullanıcıyı TC kimlik numarası,
  parola veya gereksiz sağlık detayı paylaşmamaya yönlendirir.

## Render Yayını

Canlı backend adresi:

```
https://smartlead-ai-8bj1.onrender.com
```

Uygulama Render üzerinde bir web servisi olarak çalışır. Gizli bilgiler ve
yapılandırma (`GROQ_API_KEY`, `ADMIN_API_KEY`, `DATABASE_URL`,
`CORS_ORIGINS` gibi) depoya yazılmaz; Render'ın ortam değişkenleri
üzerinden sağlanır. Böylece aynı kod tabanı yerelde SQLite, canlıda
PostgreSQL ile çalışabilir.

Servisin derleme ve başlatma ayarları Render panelinde tutulur ve bu depoda
bir yapılandırma dosyası olarak bulunmaz.

## Bilinen Sınırlamalar

- Render'ın ücretsiz web servisi bir süre trafik almadığında beklemeye
  geçer; bu nedenle ilk istekte gecikme (cold start) yaşanabilir.
- Ücretsiz PostgreSQL örneği staj/demo ortamı için kullanılmaktadır ve
  kalıcı bir üretim altyapısı olarak değerlendirilmemelidir.

## Proje Bağlantıları

- **GitHub:** https://github.com/ALCUNE/smartlead-ai
- **Backend (Render):** https://smartlead-ai-8bj1.onrender.com
- **Wix sitesi:** https://descerpeo.wixsite.com/my-site-6
