# MAX98357A I2S Ses Cikisi

MAX98357A, Raspberry Pi'den I2S uzerinden dijital ses alip dogrudan hoparlor surebilen mono amfi moduludur.

Bu proje icin onerilen ses mimarisi:

```text
USB PnP Sound Device  -> mikrofon girisi
MAX98357A I2S         -> hoparlor cikisi
```

## Baglanti

MAX98357A pinleri:

- `VIN` -> Raspberry Pi `5V`
- `GND` -> Raspberry Pi `GND`
- `BCLK` -> GPIO18 / PCM_CLK
- `LRC` veya `LRCLK` -> GPIO19 / PCM_FS
- `DIN` -> GPIO21 / PCM_DOUT

Opsiyonel:

- `GAIN`: modul dokumanina gore ses kazanci ayari
- `SD` veya `SD_MODE`: modul dokumanina gore shutdown / kanal secimi

Notlar:

- Hoparlor empedansi ve gucunu modulune gore sec.
- MAX98357A genelde mono cikis verir.
- Ses seviyesi yazilimdan kontrol edilir.
- Ortak GND sarttir.

## Pi OS Kurulum

Repo icinden:

```bash
cd ~/pi_tablet_telefon
bash device/scripts/setup-max98357a.sh
sudo reboot
```

Reboot sonrasi:

```bash
cd ~/pi_tablet_telefon
bash device/scripts/check-max98357a.sh
```

`aplay -l` ciktisinda I2S/MAX98357A benzeri bir playback cihazi gorunmeli.

## Test

Once `aplay -l` ile kart numarasini bul.

Ornek:

```bash
speaker-test -D plughw:2,0 -t wav -c 2
```

PipeWire/WirePlumber kullanan Raspberry Pi OS masaustunde:

```bash
wpctl status
wpctl set-default <sink-id>
```

Sonra Waydroid uygulamasi sesi varsayilan Pi OS cikisina gonderir.

## Geri Alma

`/boot/firmware/config.txt` icinden su satiri kaldir:

```text
dtoverlay=max98357a
```

veya script'in olusturdugu backup dosyasindan geri yukle:

```bash
sudo cp /boot/firmware/config.txt.pi-tablet-backup /boot/firmware/config.txt
sudo reboot
```
