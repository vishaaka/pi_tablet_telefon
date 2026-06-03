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

## Hailo Notu

Hailo islemleri Android/Waydroid icinde degil, bu host servis tarafinda yapilacak. Ileride kamera goruntusu veya vision pipeline eklendiginde HailoRT kullanan modul `app/hailo_runtime.py` icinde gelistirilecek.
