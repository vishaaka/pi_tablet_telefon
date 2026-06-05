# Pi Tablet Telefon

Raspberry Pi 5 tabanli, 7 inch dokunmatik ekranli, USB ses kartli ve Hailo-8/8L hizlandiricili AI telefon/tablet prototipi.

## Hedef

- Tablet benzeri tam ekran arayuz
- Android uygulamasi olarak calisan telefon deneyimi
- AI kisilerle sesli ve goruntulu gorusme
- Riza/kurgu temelli persona sistemi; gercek kisileri izinsiz taklit etmeyen tasarim

## Repo Yapisi

```text
android-phone-sim/   Android telefon simulasyonu
backend/             Raspberry Pi OS uzerinde calisacak AI/Hailo servis iskeleti
device/              Pi OS, Hailo, Waydroid ve systemd kurulum dosyalari
docs/                Mimari ve kurulum karar notlari
```

## Ilk Calisan Surum

Android app su an lokal telefon simulasyonu olarak calisir:

- Rehberde temsili AI kisiler vardir.
- Her kisinin temsili telefon numarasi vardir.
- Rehberden kisi secilip aranabilir.
- Tus takimindan numara yazilinca ilgili rehber kaydi otomatik gosterilir.
- Arama baslayinca `Araniyor` ve `Caliyor` ekranlari gelir.
- Basit calma tonu uretilir.
- Bir sure sonra AI kisi cevaplamis gibi konusma ekranina gecilir.
- Gorusme ekrani sure, sessiz, hoparlor, video ve kapatma durumlarini simule eder.

Android detaylari: [android-phone-sim/README.md](android-phone-sim/README.md)

## Ilk Teknik Karar

Android arayuz icin uygun, fakat Hailo hizlandiricinin Android uzerinde calismasi ek kernel/driver entegrasyonu gerektirebilir. Bu nedenle ilk is olarak iki asamali test yapilacak:

1. Raspberry Pi OS uzerinde Hailo donaniminin saglam calistigini dogrula.
2. Android imajinda HailoRT kutuphanesi ve PCIe driver entegrasyonu mumkun mu test et.

Ayrintilar: [docs/android-hailo-plan.md](docs/android-hailo-plan.md)

Alternatif yol: Raspberry Pi OS uzerinde Hailo'yu yerel calistirip Android uygulamalarini Waydroid ile denemek. Ayrintilar: [docs/pi-os-waydroid-hailo-plan.md](docs/pi-os-waydroid-hailo-plan.md)

## Onerilen MVP Calistirma Sirasi

1. Raspberry Pi OS 64-bit Trixie kur.
2. Hailo'yu kur ve `hailortcli fw-control identify` ile dogrula.
3. Backend'i Pi OS uzerinde calistir.
4. Waydroid kur.
5. Android APK'yi Waydroid'e yukle.
6. Telefon simulasyonu ile rehber, tus takimi ve arama ekranlarini test et.

Backend detaylari: [backend/README.md](backend/README.md)
Cihaz detaylari: [device/README.md](device/README.md)

Ilk kurulumdan itibaren adim adim bring-up: [docs/pi-bringup-step-by-step.md](docs/pi-bringup-step-by-step.md)

MAX98357A I2S hoparlor cikisi: [docs/max98357a-audio-output.md](docs/max98357a-audio-output.md)
