# Telefon Uygulamasi Ekran Akisi

## Rehber

Rehber ekrani temsili AI kisileri listeler. Her kayitta:

- Ad
- Temsili numara
- Persona kisa aciklamasi
- Ses profili
- Ara butonu

## Tus Takimi

Tus takiminda 0-9, `*` ve `#` girilebilir. Girilen rakamlar rehberdeki numaralarla eslesirse ekranda ilgili kisi paneli gosterilir.

Eslesme kurali:

- Girilen rakamlar kisinin numarasinin icinde geciyorsa eslesme vardir.
- Girilen rakamlar kisinin numarasinin sonuyla eslesiyorsa eslesme vardir.

## Arama Baslatma

Arama iki yerden baslar:

1. Rehber kaydindaki `Ara` butonu
2. Tus takimindaki `Ara` butonu

Eger tus takiminda rehber eslesmesi yoksa `Bilinmeyen Numara` isimli gecici AI arama simulasyonu baslar.

## Arama Ekranlari

Arama baslayinca ekran sirasi:

1. `Araniyor`
2. `Caliyor`
3. Otomatik cevap
4. Gorusme ekrani

Bu MVP'de cevap otomatik verilir. Ileride backend'den gelen AI oturum durumuna gore cevap gecisi yapilacak.

## Gorusme Ekrani

Gorusme ekraninda:

- Kisi adi
- Persona bilgisi
- Gorusme suresi
- Sessiz / mikrofon ac
- Hoparlor / ahize
- Video ac / kapat
- Tuslar
- Kapat

`Video` butonu bu asamada gercek kamera veya avatar akisi baslatmaz; sadece goruntulu arama durumunu simule eder.

## Sonraki Gelistirme

- Android app -> backend WebSocket baglantisi
- Mikrofon kaydi
- STT
- LLM persona cevabi
- TTS
- Avatar / video state eventleri
- Hailo vision pipeline entegrasyonu
