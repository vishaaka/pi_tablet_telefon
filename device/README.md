# Cihaz Kurulumu

Hedef cihaz:

- Raspberry Pi 5 2GB
- Raspberry Pi OS 64-bit Trixie
- Hailo-8/8L
- 7 inch dokunmatik ekran
- USB ses karti
- Waydroid

## Sira

1. Raspberry Pi OS 64-bit Trixie kur.
2. `scripts/00-first-boot-check.sh` ile ilk durumu kaydet.
3. `scripts/01-system-update.sh` ile sistemi guncelle.
4. `scripts/02-audio-check.sh` ile USB ses kartini kontrol et.
5. `scripts/install-hailo.sh` ile Hailo paketlerini kur.
6. `scripts/verify-hailo.sh` ile donanimi dogrula.
7. Backend servisini kur.
8. `scripts/install-waydroid.sh` ile Waydroid kurulumunu dene.
9. Android APK'yi Waydroid icine yukle.

## MAX98357A I2S Hoparlor

USB ses kartini mikrofon girisi, MAX98357A'yi hoparlor cikisi olarak kullanmak icin:

```bash
bash device/scripts/setup-max98357a.sh
sudo reboot
bash device/scripts/check-max98357a.sh
```

Ayrinti: `docs/max98357a-audio-output.md`

## INMP441 I2S Mikrofon

INMP441'i mikrofon girisi olarak denemek icin:

```bash
bash device/scripts/setup-inmp441-googlevoicehat-experimental.sh
sudo reboot
bash device/scripts/check-inmp441.sh
```

Ayrinti: `docs/inmp441-i2s-mic.md`

## Backend Servisi

Servisi mevcut kullanici ve repo konumuna gore otomatik olusturmak icin:

```bash
bash device/scripts/install-backend-service.sh ~/pi_tablet_telefon
curl http://127.0.0.1:8080/health
```

## Acilista Otomatik Telefon

Pi acildiginda backend, ses seviyesi, Waydroid ve Pi Telefon uygulamasini hazir hale getirmek icin:

```bash
bash device/scripts/install-phone-autostart-service.sh ~/pi_tablet_telefon
```

Kontrol:

```bash
systemctl status pi-tablet-phone-autostart --no-pager
tail -n 80 ~/pi-tablet-phone-autostart.log
```
