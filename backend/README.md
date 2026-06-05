# Pi Host Backend

Bu servis Raspberry Pi OS uzerinde calisir. Android telefon uygulamasi Waydroid icinden bu servise HTTP/WebSocket ile baglanacak sekilde tasarlanir.

Bu ilk surum gercek AI modeli calistirmaz; telefon uygulamasinin baglanabilecegi stabil bir API iskeleti verir.

## Calistirma

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Uclar

- `GET /health`
- `GET /contacts`
- `POST /calls/start`
- `POST /calls/{call_id}/message`
- `POST /calls/{call_id}/end`

## AI Persona Baglantisi

Varsayilan mod yereldir; API anahtari olmadan her rehber kisisi kendi persona metniyle temsili cevap verir.

OpenAI uyumlu bir servis baglamak icin systemd servisine veya shell'e su degiskenleri eklenebilir:

```bash
export PI_AI_PROVIDER=openai
export OPENAI_API_KEY=...
export PI_AI_MODEL=gpt-4o-mini
```

Opsiyonel:

```bash
export PI_AI_API_BASE=https://api.openai.com/v1
```

Her arama `POST /calls/start` ile kisinin persona oturumunu acar. `POST /calls/{call_id}/message` ayni kisiye ait konusma gecmisini kullanarak cevap verir.

Gemini baglamak icin:

```bash
export PI_AI_PROVIDER=gemini
export GEMINI_API_KEY=...
export PI_AI_MODEL=gemini-flash-latest
```

## TTS

Hugging Face Space uzerinden Edge TTS baglamak icin:

```bash
export PI_TTS_ENABLED=true
export PI_TTS_PROVIDER=hf_space
export HF_TTS_SPACE=innoai/Edge-TTS-Text-to-Speech
export HF_TTS_API_NAME=/tts_interface
```

Kisilerin `tts_voice`, `tts_rate` ve `tts_pitch` alanlari farkli sesleri belirler. Uretilen dosyalar `/audio/...` URL'si ile servis edilir.

TTS dosyalari `ffmpeg` varsa varsayilan olarak yukseltilir ve limiter'dan gecer. Seviyeyi ayarlamak icin:

```bash
export PI_TTS_AUDIO_BOOST=true
export PI_TTS_GAIN_DB=8
```

## Hailo Notu

Hailo islemleri Android/Waydroid icinde degil, bu host servis tarafinda yapilacak. Ileride kamera goruntusu veya vision pipeline eklendiginde HailoRT kullanan modul `app/hailo_runtime.py` icinde gelistirilecek.
