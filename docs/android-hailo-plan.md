# Android ve Hailo Kurulum Plani

## Donanim

- Raspberry Pi 5 2GB
- Hailo-8 veya Hailo-8L M.2 / AI HAT
- 7 inch dokunmatik ekran
- USB plug and play ses karti
- Mikrofon ve hoparlor
- Tercihen resmi 27W Raspberry Pi guc adaptoru
- Aktif sogutucu

Not: Pi 5 2GB Android + sesli AI gorusme icin sinirda kalabilir. Ilk prototipte AI model calistirma isini bulut veya ayri Linux backend'e almak daha guvenli.

## Android Kurulumu

Raspberry Pi 5 icin yaygin secenekler:

- KonstaKANG AOSP / LineageOS Android tablet imajlari
- Emteria Android

Tablet/dokunmatik kullanim icin Android TV yerine AOSP veya LineageOS tablet imaji tercih edilecek.

Ilk hedef:

1. Android imajini microSD veya NVMe'ye yaz.
2. 7 inch ekran dokunmatik calisiyor mu test et.
3. USB ses karti giris/cikis cihazlari gorunuyor mu test et.
4. Basit bir Android test uygulamasi ile mikrofon kaydi ve hoparlor cikisi dene.
5. Sonra telefon uygulamasi MVP'sini yukle.

## Hailo Durumu

Hailo tarafinda kritik nokta sudur: Android destegi teorik olarak var, fakat Raspberry Pi Android imajinda Hailo'nun calismasi icin iki parca gerekir:

- Android icin derlenmis HailoRT user-space kutuphanesi
- Android kernel'ine entegre edilmis veya modul olarak yuklenmis HailoRT PCIe driver

Bu ikisi Android imajinda yoksa Hailo-8/8L plug and play calismaz.

Bu yuzden once Raspberry Pi OS ile donanim dogrulama yapilacak.

## Hailo Donanim Dogrulama

Raspberry Pi OS 64-bit uzerinde:

```bash
sudo apt update
sudo apt install hailo-all
sudo reboot
hailortcli fw-control identify
```

Beklenen sonuc: Hailo cihazi listelenmeli ve firmware bilgisi okunmali.

Ek kontrol:

```bash
lspci | grep -i hailo
```

Bu asama basarisiz olursa Android'e gecmeden once guc, sogutma, HAT baglantisi, PCIe ayarlari ve driver kurulumu cozulecek.

## Onerilen Mimari

### MVP

Android sadece arayuz ve ses/goruntu istemcisi olur.

- Android uygulamasi: arama ekrani, kisiler, mikrofon/kamera
- Backend: STT, LLM, TTS, persona yonetimi
- Hailo: ilk etapta devre disi veya Linux backend tarafinda

### Hailo Calisirsa

Hailo yerelde su islerde kullanilabilir:

- Yuz/nesne algilama
- Kamera goruntusu uzerinde vision inference
- Avatar/goruntulu arama icin yardimci vision pipeline'lari

Hailo-8/8L, ana LLM ve kaliteli TTS icin dogrudan ideal parca degildir. Sesli sohbet motorunu ayri backend veya bulut uzerinden planlamak daha gercekci.

## Karar

Android kurulumuna devam edilecek, fakat Hailo icin once Raspberry Pi OS dogrulama testi yapilacak. Hailo Android altinda calismazsa uygulama mimarisi Android client + Linux/Cloud AI backend olarak ilerleyecek.

## Kaynaklar

- https://konstakang.com/devices/rpi5/
- https://github.com/hailo-ai/hailort
- https://github.com/hailo-ai/hailo-rpi5-examples/blob/main/doc/install-raspberry-pi5.md
- https://www.raspberrypi.com/documentation/computers/ai.html
- https://community.hailo.ai/t/using-hailo-in-android/9030
