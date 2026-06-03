# Android Telefon Simulasyonu

Bu uygulama Waydroid veya normal Android cihazda calisacak telefon simulasyonudur.

## Ozellikler

- Android benzeri rehber listesi
- Temsili AI kisiler ve numaralar
- Tus takimindan numara yazma
- Yazilan numaraya gore rehber kaydini otomatik bulma
- Araniyor / caliyor ekran gecisleri
- Ton uretimi ile basit calma sesi
- Otomatik cevaplanan AI gorusme simulasyonu
- Sesli/goruntulu arama ekran durumlari
- Sessiz, hoparlor, video ve kapatma kontrolleri

## Build

Android Studio ile `android-phone-sim` klasorunu acip `app` modulunu calistirin.

Komut satiri icin Android SDK ve Gradle kuruluysa:

```bash
cd android-phone-sim
gradle assembleDebug
```

Olusan APK:

```text
app/build/outputs/apk/debug/app-debug.apk
```

## Waydroid'e Yukleme

```bash
waydroid app install app/build/outputs/apk/debug/app-debug.apk
waydroid app launch com.vishaaka.pitablettelefon
```

## Sonraki Asama

Bu MVP ekranda tum arama akislarini lokal simule eder. Sonraki adimda backend'e WebSocket ile baglanip STT/LLM/TTS cevaplarini gercek zamanli almak eklenecek.
