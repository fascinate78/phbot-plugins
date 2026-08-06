# FCaravanNavigator V3

FCaravanNavigator V3, phBot karakterini önceden tanımlanmış şehir ve özel noktalara otomatik götürmek için hazırlanmış bir kervan navigasyon eklentisidir. Mevcut sürüm `3.0.0`dır.

Eklenti hedef koordinata giden rotayı phBot'un yol bulma sistemiyle üretir, oluşan scripti çalıştırır ve yolculuğun durumunu arayüzde canlı olarak gösterir. Rota yürüyüş, teleport veya ferry/kervan geçişleri içerebilir.

## Temel çalışma biçimi

1. Kullanıcı arayüzden bir hedef seçer.
2. Eklenti çalışan scripti durdurur ve `generate_script` ile hedefe yeni bir rota üretir.
3. Üretilen komutlar phBot scripti olarak başlatılır.
4. Karakterin region ve koordinatları düzenli olarak kontrol edilir.
5. Karakter hedefle aynı region içinde ve hedefe en fazla `20` birim uzaktaysa yolculuk tamamlanmış sayılır.

Arka arkaya gereksiz rota hesaplanmasını önlemek için yol bulma işlemleri arasında `6` saniyelik bekleme süresi vardır.

## Hazır hedefler

### Şehirler

| Hedef | Region | X | Y | Z |
| --- | ---: | ---: | ---: | ---: |
| Jangan | 25000 | 6504 | 1004 | 0 |
| Donwhang | 26265 | 3502 | 2081 | -106 |
| Hotan | 23687 | 148 | 82 | 243 |

### Özel noktalar

| Hedef | Region | X | Y | Z |
| --- | ---: | ---: | ---: | ---: |
| Roc Special | 23411 | -3798 | -190 | 2626 |
| Bandit Special | 23712 | 4840 | 140 | 1384 |
| Taklamakan Special | 26753 | -1134 | 2458 | 112 |

Hedefler `FCaravanNavigatorV3.py` içindeki `locations` listesinde tanımlıdır. Yeni bir hedef eklemek için aşağıdaki yapıda bir kayıt eklenebilir:

```python
{
    "name": "Hedef Adı",
    "category": "town",
    "region": 25000,
    "x": 6504,
    "y": 1004,
    "z": 0
}
```

`category` yalnızca `town` veya `special` olabilir. Eksik alanı, geçersiz kategorisi ya da sayısal olmayan koordinatı bulunan kayıtlar yüklenmez ve hata phBot günlüğüne yazılır.

## Arayüz

### Route Controls

- `Reload Locations`: Python dosyasındaki hedef listesini yeniden doğrular ve hedef düğmelerini tekrar oluşturur.
- `Stop Navigation`: Çalışan rota scriptini ve aktif navigasyon takibini durdurur.
- `Settings`: Ses, ölüm güvenliği, saldırgan takibi ve harici bildirim seçeneklerini açar.
- `Destinations`: Ayarlar ekranından hedef listesine geri döner.

`Reload Locations` harici bir JSON dosyası okumaz. Çalışan eklentinin belleğindeki `locations` listesini yeniden yükler; kaynak kod değiştirildiyse normalde eklentinin de yeniden yüklenmesi gerekir.

### Live Navigation

Sağ taraftaki canlı durum panelinde şunlar gösterilir:

- Seçilen hedef
- Navigasyon durumu
- Geçen veya tamamlanan yolculuk süresi
- Rota türü
- Son tespit edilen oyuncu saldırgan

Olası rota türleri:

- `CARAVAN / FERRY`: Üretilen teleport komutlarından en az biri `FERRY` içerir.
- `TELEPORT ROUTE`: Rota teleport komutu içerir.
- `WALK ONLY`: Rota yalnızca hareket komutlarından oluşur.

## Yolculuk güvenliği

Eklenti, aktif navigasyon sırasında karakter ve transport ölüm eventlerini izler.

### Karakter öldüğünde

`Stop on character death` açıksa rota scripti durdurulur. Yolculuk süresi ve varsa yakın zamanda tespit edilmiş oyuncu saldırgan arayüzde ve günlükte gösterilir.

Seçenek kapalıysa navigasyon otomatik olarak durdurulmaz; ancak etkin harici bildirim kanallarına ölüm bilgisi gönderilir.

### Transport öldüğünde

Transport ölüm eventi geldiğinde eklenti `1,5` saniye bekleyerek olayı doğrular. Bu sırada:

- Yaşayan bir transport hâlâ bulunuyorsa event yok sayılır.
- Karakter region değiştirmişse olay geçiş kaynaklı kabul edilerek yok sayılır.
- Ölüm doğrulanır ve `Stop on transport death` açıksa navigasyon güvenlik amacıyla durdurulur.

Bu doğrulama, ferry veya region geçişlerinde oluşabilecek hatalı transport ölüm eventlerinin rotayı gereksiz yere kesmesini azaltır.

### Saldırgan takibi

`Track last player attacker` açıksa navigasyon sırasında oyuncu saldırı eventleri kaydedilir. Son saldırgan varsayılan olarak `15` saniye hatırlanır. Bu süre ayarlardan `1-300` saniye arasında değiştirilebilir.

Karakter veya transport bu süre içinde ölürse saldırgan adı olay kaydına ve bildirim mesajına eklenir. Oyuncu saldırgan bulunamazsa olay `Unknown / NPC` olarak gösterilir.

## Varış bildirimi

Karakter hedefe ulaştığında eklenti:

- Navigasyonu `ARRIVED` durumuna geçirir.
- Yolculuk süresini gösterir.
- Oyun istemcisinde varış bildirimi gösterir.
- Etkinse seçilen WAV sesini çalar.
- Etkin Discord ve Telegram kanallarına varış mesajı yollar.

### WAV sesi ekleme

1. phBot yapılandırma dizinindeki `FCaravanNavigator V3/Sounds` klasörünü açın.
2. Kullanılacak `.wav` dosyasını bu klasöre kopyalayın.
3. Ayarlar ekranında `Refresh` düğmesine basın.
4. Sesi listeden seçip `Test Sound` ile deneyin.
5. `Enable arrival sound` seçeneğini açın ve ayarları kaydedin.

Yalnızca `.wav` uzantılı dosyalar listelenir.

## Discord bildirimleri

Discord bildirimleri için geçerli bir HTTPS webhook adresi gerekir. Adres `/api/webhooks/` bölümünü içermelidir.

1. `Enable Discord` seçeneğini açın.
2. Webhook adresini girin.
3. `Test Discord` ile deneme mesajı gönderin.
4. `Save Settings` ile kaydedin.

Bildirim isteği ayrı bir arka plan thread'inde ve `5` saniyelik bağlantı zaman aşımıyla gönderilir; böylece navigasyon döngüsü ağ isteği yüzünden beklemez.

## Telegram bildirimleri

Telegram ekranına `Telegram →` düğmesiyle geçilir.

1. `Enable Telegram notifications` seçeneğini açın.
2. Bot token değerini girin.
3. Mesajın gönderileceği Chat ID değerini girin.
4. `Test Telegram` ile bağlantıyı deneyin.
5. `Save Telegram` ile kaydedin.

Telegram isteği de ayrı bir thread'de gönderilir. Sertifika doğrulama hatası oluşursa eklenti uyumluluk amacıyla doğrulamasız SSL bağlantısını bir kez deneyebilir.

## Ayarlar

| Ayar | Varsayılan | Açıklama |
| --- | --- | --- |
| `arrival_sound_enabled` | `true` | Varışta seçilen WAV dosyasını çalar. |
| `arrival_sound` | boş | Kullanılacak WAV dosyasının adıdır. |
| `stop_on_character_death` | `true` | Karakter ölünce navigasyonu durdurur. |
| `stop_on_transport_death` | `true` | Transport ölümü doğrulanınca navigasyonu durdurur. |
| `attacker_tracking_enabled` | `true` | Son oyuncu saldırganı takip eder. |
| `attacker_memory_seconds` | `15` | Saldırganın kaç saniye hatırlanacağını belirler. |
| `discord_notifications_enabled` | `false` | Discord bildirimlerini etkinleştirir. |
| `discord_webhook_url` | boş | Discord webhook adresidir. |
| `telegram_notifications_enabled` | `false` | Telegram bildirimlerini etkinleştirir. |
| `telegram_bot_token` | boş | Telegram bot erişim token değeridir. |
| `telegram_chat_id` | boş | Telegram hedef sohbet kimliğidir. |

Ayarlar phBot yapılandırma klasöründeki aşağıdaki dosyada tutulur:

```text
FCaravanNavigator V3/settings.json
```

Ses dosyaları ise şu klasörde aranır:

```text
FCaravanNavigator V3/Sounds/
```

## Güvenlik ve kullanım notları

- Discord webhook adresi ve Telegram bot token değeri `settings.json` içinde düz metin olarak saklanır. Dosyayı paylaşmayın ve kaynak kontrolüne eklemeyin.
- Rota başarısı phBot yol bulma verisine, mevcut bölge bağlantılarına ve hedef sunucunun teleport/ferry tanımlarına bağlıdır.
- Bir hedef düğmesine basıldığında o anda çalışan phBot scripti önce durdurulur.
- Hedefte yalnızca X/Y mesafesi ölçülür; Z değeri rota üretiminde kullanılsa da varış kontrolüne dahil edilmez.
- `Stop Navigation` karakteri veya transportu fiziksel olarak durdurmak yerine çalışan phBot rota scriptini sonlandırır.
- Harici bildirimler için phBot ortamının internete çıkabilmesi gerekir.
