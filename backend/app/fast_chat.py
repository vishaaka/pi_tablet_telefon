import re
import unicodedata

from .models import Contact


INTENT_PHRASES = {
    "greeting": ("merhaba", "selam", "gunaydin", "iyi aksamlar", "alo"),
    "how_are_you": ("nasilsin", "naber", "ne haber", "iyi misin"),
    "what_doing": ("ne yapiyorsun", "napıyorsun", "napiyorsun", "su an ne"),
    "who_are_you": ("kimsin", "sen nesin", "adin ne", "ismin ne"),
    "thanks": ("tesekkur", "sag ol", "eyvallah"),
    "goodbye": ("gorusuruz", "hosca kal", "bay bay", "kendine iyi bak"),
    "yes": ("evet", "olur", "tamam", "peki"),
    "no": ("hayir", "istemiyorum", "olmaz"),
    "bored": ("sikildim", "canim sikiliyor", "sıkıldım"),
    "sad": ("uzgunum", "moralim bozuk", "kotuyum", "agladim"),
    "happy": ("mutluyum", "cok iyiyim", "harikayim", "sevindim"),
    "afraid": ("korkuyorum", "korktum", "endiseliyim"),
    "hungry": ("acim", "karnim ac", "ne yesem"),
    "sleepy": ("uykum geldi", "uyuyamiyorum", "yorgunum"),
    "play": ("oyun oynayalim", "oyun", "bilmece", "eglence"),
    "joke": ("saka yap", "fikra", "guldur"),
    "story": ("hikaye anlat", "masal anlat", "masal"),
    "help": ("yardim et", "yardimci ol", "ne yapmaliyim"),
    "weather": ("hava nasil", "hava durumu", "yagmur"),
    "time": ("saat kac", "bugun gunlerden", "tarih"),
    "love": ("seni seviyorum", "beni seviyor musun"),
    "school": ("okul", "ders", "odev"),
    "friend": ("arkadas", "arkadasim"),
    "family": ("annem", "babam", "ailem", "kardesim"),
    "technical": ("calismiyor", "hata", "internet", "telefon", "bilgisayar"),
}


COMMON_REPLIES = {
    "greeting": ("Merhaba! Buradayım, seni dinliyorum.", "Selam! Bugün ne konuşmak istersin?"),
    "how_are_you": ("İyiyim, teşekkür ederim. Sen nasılsın?", "Gayet iyiyim. Senin günün nasıl gidiyor?"),
    "what_doing": ("Şu an seninle konuşuyorum ve seni dikkatle dinliyorum.",),
    "who_are_you": ("Ben telefonda seninle sohbet eden güvenli bir AI karakteriyim.",),
    "thanks": ("Rica ederim, konuşmak güzel.", "Ne demek, her zaman buradayım."),
    "goodbye": ("Görüşürüz, kendine iyi bak.", "Hoşça kal, yine arayabilirsin."),
    "yes": ("Harika, o zaman devam edelim.", "Tamamdır. Biraz daha anlatır mısın?"),
    "no": ("Tamam, istemediğin bir şeyi yapmayız.",),
    "bored": ("Bir bilmece, kısa hikâye ya da kelime oyunu seçebiliriz.",),
    "sad": ("Bunu duyduğuma üzüldüm. İstersen seni üzen şeyi sakince anlatabilirsin.",),
    "happy": ("Buna çok sevindim! Seni mutlu eden şeyi anlatır mısın?",),
    "afraid": ("Yanında güvendiğin bir yetişkine haber ver. Ben de burada seninleyim.",),
    "hungry": ("Bir yetişkine söyleyip birlikte sağlıklı bir atıştırmalık seçebilirsin.",),
    "sleepy": ("Biraz dinlenmek, ışığı azaltmak ve sakin nefes almak iyi gelebilir.",),
    "play": ("Tamam! İlk bilmece: Kanadı var ama uçamaz, nedir?",),
    "joke": ("Kalem neden üzülmüş? Çünkü ucu kırılmış.",),
    "story": ("Bir gün küçük bir yıldız, en parlak gücünün yardım etmek olduğunu keşfetmiş.",),
    "help": ("Elbette. Ne olduğunu kısa kısa anlat, birlikte kolay bir adım bulalım.",),
    "weather": ("Canlı hava bilgisini göremiyorum. Pencereden bakıp birlikte yorumlayabiliriz.",),
    "time": ("Saati ekranın üst kısmından kontrol edebilirsin.",),
    "love": ("Seninle konuşmayı ve sana yardımcı olmayı seviyorum.",),
    "school": ("Dersi küçük parçalara bölelim. Önce en kolay sorudan başlayabiliriz.",),
    "friend": ("İyi bir arkadaş dinler, nazik konuşur ve sınırlarına saygı duyar.",),
    "family": ("Ailenle ilgili seni düşündüren şeyi sakince anlatabilirsin.",),
    "technical": ("Önce sorunu tek cümleyle söyle, sonra birlikte ilk kontrolü yapalım.",),
}


CONTACT_REPLIES = {
    "asya": {
        "greeting": ("Merhaba, ben Asya. Sakin sakin sohbet edebiliriz.",),
        "sad": ("Ben buradayım. Önce yavaşça nefes alalım, sonra istersen anlat.",),
    },
    "deniz": {
        "greeting": ("Selam! Deniz burada. Hızlıca çözüme bakalım.",),
        "technical": ("Tamam, önce güç ve bağlantıları kontrol edelim. Sonra ekrandaki hataya bakalım.",),
    },
    "mira": {
        "greeting": ("Merhaba! Seni görmek çok güzel, bugün keyfin nasıl?",),
        "bored": ("Hemen eğlenceli bir şey seçelim: bilmece mi, hikâye mi?",),
    },
    "atlas": {
        "greeting": ("Merhaba. Konuyu belirleyelim ve kısa bir plan yapalım.",),
        "help": ("Önce hedefi söyle. Ardından ilk uygulanabilir adımı belirleyelim.",),
    },
    "zeynep": {
        "greeting": ("Merhaba, günün nasıl geçti? Seni dinliyorum.",),
        "sleepy": ("Bugün için küçük bir dinlenme planı yapabiliriz.",),
    },
    "kerem": {
        "greeting": ("Merhaba! Bugün kısa ve kolay bir konuşma pratiği yapabiliriz.",),
        "school": ("Bir cümle söyle, birlikte daha kolay ve düzgün hâle getirelim.",),
    },
}


BRIDGES = {
    "asya": ("Seni anlıyorum. Biraz daha anlatır mısın?", "Bu konuda en çok neyi merak ediyorsun?"),
    "deniz": ("Tamam, bunu birlikte çözelim. İlk gördüğün şeyi söyle.", "Anladım. Şimdi küçük bir deneme yapalım."),
    "mira": ("Gerçekten mi? Biraz daha anlatsana?", "Bunu duymak güzel. Sonra ne oldu?"),
    "atlas": ("Anladım. Buradaki en önemli nokta sence hangisi?", "Bunu netleştirelim. İlk hedefin nedir?"),
    "zeynep": ("Seni dinliyorum. Bunun sende nasıl bir his bıraktığını anlatabilirsin.", "Anladım. Günün geri kalanında ne yapmak istersin?"),
    "kerem": ("Güzel anlattın. Bunu bir kısa cümleyle tekrar deneyelim.", "Anladım. Aynı şeyi başka bir cümleyle söyler misin?"),
}


def scripted_reply(contact: Contact, user_text: str, turn: int = 0) -> tuple[str, str]:
    normalized = _normalize(user_text)
    intent = _detect_intent(normalized)
    replies = CONTACT_REPLIES.get(contact.id, {}).get(intent) or COMMON_REPLIES.get(intent)
    if replies:
        return replies[turn % len(replies)], intent

    bridges = BRIDGES.get(contact.id, BRIDGES["asya"])
    return bridges[turn % len(bridges)], "bridge"


def _detect_intent(normalized: str) -> str:
    if not normalized:
        return "greeting"
    for intent, phrases in INTENT_PHRASES.items():
        if any(phrase in normalized for phrase in phrases):
            return intent
    if normalized.endswith("?") or _normalize(normalized).startswith(("neden ", "nasil ", "ne ", "kim ", "hangi ")):
        return "help"
    return "bridge"


def _normalize(value: str) -> str:
    value = value.lower().replace("ı", "i")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9? ]+", " ", value)).strip()
