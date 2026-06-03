# Raspberry Pi OS + Waydroid + Hailo Plani

## Kisa Cevap

Evet, Android uygulamalarini yukleyebilecegimiz ve ayni zamanda Hailo icin resmi Raspberry Pi OS desteginden yararlanabilecegimiz bir yol var:

- Ana isletim sistemi: Raspberry Pi OS 64-bit Trixie
- Android uygulama katmani: Waydroid
- Hailo katmani: Raspberry Pi OS uzerinde `hailo-all`, HailoRT ve yerel backend servisleri

Bu, Hailo'yu Android'in icinde calistirmaya calismaktan daha gercekci bir mimari.

## Neden Bu Yol?

Android imaji kullanirsak Hailo icin Android kernel driver entegrasyonu gerekir. Bu zor ve imaja bagimlidir.

Raspberry Pi OS kullanirsak Hailo resmi paketlerle desteklenir. Android uygulamasi ise Waydroid icinde calisir. Android app, Hailo'ya dogrudan erismek yerine `localhost` veya yerel ag uzerinden Linux host'taki backend servise konusur.

## Mimari

```text
Raspberry Pi OS 64-bit Trixie
  |
  |-- Hailo driver + HailoRT + hailo-all
  |-- AI backend service
  |     |-- Hailo vision pipeline
  |     |-- STT / LLM / TTS baglantilari
  |
  |-- Waydroid Android container
        |-- Telefon Android app
        |-- Mikrofon / kamera / dokunmatik UI
        |-- Backend'e HTTP/WebSocket ile baglanir
```

## Ilk Kurulum Sirasi

1. Raspberry Pi OS 64-bit Trixie kur.
2. Sistemi guncelle.
3. Hailo'yu kur ve dogrula.
4. Waydroid kur.
5. Android app yukleme ve ses/kamera testlerini yap.
6. Android app'ten Linux host'taki backend'e baglan.

## Hailo Kurulum Testi

```bash
sudo apt update
sudo apt install dkms
sudo apt install hailo-all
sudo reboot
hailortcli fw-control identify
lspci | grep -i hailo
```

AI Kit kullaniliyorsa PCIe Gen 3.0 ayari da yapilacak.

## Waydroid Notlari

Waydroid, Wayland tabanli Linux masaustu uzerinde Android OS container calistirir. Raspberry Pi OS 64-bit kullanilmasi gerekir. Pi-Apps uzerinden kurulumu pratik olabilir.

Riskler:

- Pi 5 2GB RAM sinirda kalabilir.
- Google Play gerektiren uygulamalar ekstra adim ister.
- Bazi Android uygulamalarinda GPU, kamera, mikrofon veya DRM sorunlari olabilir.
- Hailo cihazi Waydroid icinden dogrudan kullanmak hedeflenmemeli; host backend kullanilmali.

## Proje Icin Karar

Ana prototip icin onerilen yol:

1. Raspberry Pi OS 64-bit Trixie + Hailo resmi kurulum
2. Waydroid ile Android telefon app testi
3. Hailo ve AI servislerini Linux host'ta tutma
4. Android app'i sadece UI, ses, goruntu ve kontrol istemcisi yapma

Bu mimari basarili olursa Android app deneyimini koruruz, Hailo'yu da resmi destekli Linux tarafinda calistiririz.

## Kaynaklar

- https://www.raspberrypi.com/documentation/computers/ai.html
- https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html
- https://pi-apps.io/install-app/install-waydroid-on-raspberry-pi/
- https://pimylifeup.com/raspberry-pi-waydroid/
- https://github.com/waydroid/waydroid/issues/2047
