# Raspberry Pi Bring-up Rehberi

Bu rehber Raspberry Pi 5 uzerinde ilk kurulumdan telefon simulasyonu APK'sini Waydroid'e yuklemeye kadar izlenecek sirayi verir.

## Hedef Mimari

```text
Raspberry Pi OS 64-bit Trixie
  |
  |-- Hailo driver + HailoRT
  |-- Pi Tablet Telefon backend
  |-- Waydroid
        |-- Pi Telefon Android app
```

## 0. Hazirlik

Gerekli donanim:

- Raspberry Pi 5 2GB
- Hailo-8/8L AI Kit veya AI HAT/HAT+
- 7 inch HDMI veya DSI dokunmatik ekran
- USB ses karti
- Mikrofon ve hoparlor
- Resmi veya kaliteli 5V 5A / 27W guc adaptoru
- Aktif sogutma
- microSD veya NVMe

Onerilen imaj:

- Raspberry Pi OS 64-bit Trixie with Desktop

Raspberry Pi Imager ayarlari:

- Hostname: `pi-tablet`
- SSH: acik
- Kullanici: `pi`
- Wi-Fi: gerekiyorsa tanimli
- Locale/keyboard: kendi bolgene gore

## 1. Ilk Acilis Kontrolu

Pi acildiktan sonra terminalde:

```bash
uname -a
cat /etc/os-release
free -h
vcgencmd get_throttled
```

Beklenen:

- OS 64-bit olmali.
- Debian/Raspberry Pi OS Trixie olmali.
- `vcgencmd get_throttled` mumkunse `0x0` donmeli.

Repo Pi uzerinde yoksa:

```bash
sudo apt update
sudo apt install -y git
git clone https://github.com/vishaaka/pi_tablet_telefon.git ~/pi_tablet_telefon
cd ~/pi_tablet_telefon
```

## 2. Sistem Guncelleme

```bash
cd ~/pi_tablet_telefon
bash device/scripts/01-system-update.sh
sudo reboot
```

Reboot sonrasi:

```bash
cd ~/pi_tablet_telefon
bash device/scripts/00-first-boot-check.sh
```

## 3. Ekran, Dokunmatik ve Ses Kontrolu

```bash
cd ~/pi_tablet_telefon
bash device/scripts/02-audio-check.sh
```

Ses karti gorunmeli. Test icin:

```bash
speaker-test -t wav -c 2
arecord -l
aplay -l
```

Dokunmatik icin:

```bash
libinput list-devices
```

## 4. Hailo Kurulumu

```bash
cd ~/pi_tablet_telefon
bash device/scripts/install-hailo.sh
sudo reboot
```

Reboot sonrasi:

```bash
cd ~/pi_tablet_telefon
bash device/scripts/verify-hailo.sh
```

Beklenen:

- `lspci` Hailo cihazini gostermeli.
- `hailortcli fw-control identify` cihaz bilgisini okumali.

## 5. Backend Kurulumu

```bash
cd ~/pi_tablet_telefon
bash device/scripts/install-backend.sh ~/pi_tablet_telefon
```

Elle test:

```bash
cd ~/pi_tablet_telefon/backend
. .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Baska terminalden:

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/contacts
```

Servis olarak calistirma:

```bash
sudo cp ~/pi_tablet_telefon/device/systemd/pi-tablet-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pi-tablet-backend
systemctl status pi-tablet-backend
```

## 6. Waydroid Kurulumu

Pi-Apps ile Waydroid kurulumu onerilir:

```bash
cd ~/pi_tablet_telefon
bash device/scripts/install-waydroid.sh
```

Pi-Apps kurulu degilse:

```bash
git clone https://github.com/Botspot/pi-apps ~/pi-apps
~/pi-apps/install
```

Sonra Pi-Apps icinden Waydroid kur.

Waydroid test:

```bash
waydroid status
waydroid session start
waydroid show-full-ui
```

## 7. Android APK Yukleme

APK Pi uzerinde yoksa Windows makineden veya GitHub artifact olarak kopyalanacak.

APK Pi uzerindeyse:

```bash
waydroid app install app-debug.apk
waydroid app launch com.vishaaka.pitablettelefon
```

## 8. Ilk Kabul Testi

Uygulamada:

1. Rehberi ac.
2. Bir AI kisiyi ara.
3. `Araniyor` ekranini gor.
4. `Caliyor` ekranini gor.
5. Otomatik gorusme ekranina gecmesini bekle.
6. `Video`, `Sessiz`, `Hoparlor`, `Kapat` butonlarini dene.
7. Tus takimindan `532101` yaz ve `Asya AI` kaydi geliyor mu bak.

## Sorun Kaydi

Her adimda sorun cikarsa su komutlarin ciktilarini kaydet:

```bash
uname -a
cat /etc/os-release
vcgencmd get_throttled
lspci
lsusb
aplay -l
arecord -l
systemctl status pi-tablet-backend
waydroid status
```

## Kaynaklar

- https://www.raspberrypi.com/documentation/computers/ai.html
- https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html
- https://www.raspberrypi.com/news/software-updates-for-raspberry-pi-ai-products/
- https://pi-apps.io/install-app/install-waydroid-on-raspberry-pi/
