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
    "why": ("neden", "niye"),
    "favorite": ("en sevdigin", "favorin", "en cok neyi seversin"),
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

FOLLOW_UPS = {
    "play": {
        "yes": "Harika! Bilmece geliyor: Ağzı var konuşmaz, yatağı var uyumaz. Nedir?",
        "no": "Tamam, oyun oynamayalım. Bugün olan güzel bir şeyi anlatmak ister misin?",
    },
    "story": {
        "yes": "O zaman devam edelim. Küçük yıldız, arkadaşına yol göstermek için bütün gece parlamış.",
        "no": "Tamam, hikâyeyi burada bırakalım. Başka ne konuşmak istersin?",
    },
    "bored": {
        "yes": "Süper. Bilmece mi, kısa hikâye mi seçersin?",
        "no": "Peki. İstersen bugün gördüğün ilginç bir şeyi anlatabilirsin.",
    },
    "sad": {
        "yes": "Seni dinliyorum. Seni üzen şeyin en zor kısmı neydi?",
        "no": "Tamam, anlatmak zorunda değilsin. Birlikte daha güzel bir konu seçebiliriz.",
    },
    "technical": {
        "yes": "Güzel. Şimdi ekranda gördüğün ilk şeyi söyle, oradan devam edelim.",
        "no": "Tamam. Başka bir çözüm deneyelim; cihaz açık mı?",
    },
}

FAVORITES = {
    "asya": "Ben en çok sakin müzikleri ve güzel hikâyeleri severim.",
    "deniz": "Ben çalışan bir şeyi düzeltmeyi ve yeni teknolojileri severim.",
    "mira": "Ben renkli resimleri, eğlenceli hikâyeleri ve sohbet etmeyi severim.",
    "atlas": "Ben iyi hazırlanmış planları ve tamamlanan işleri severim.",
    "zeynep": "Ben huzurlu yürüyüşleri ve günün güzel anlarını severim.",
    "kerem": "Ben yeni kelimeler öğrenmeyi ve farklı diller duymayı severim.",
}


def scripted_reply(
    contact: Contact,
    user_text: str,
    turn: int = 0,
    context: dict[str, str] | None = None,
) -> tuple[str, str]:
    context = context if context is not None else {}
    normalized = _normalize(user_text)
    intent = _detect_intent(normalized)

    name = _extract_name(user_text)
    if name:
        context["user_name"] = name
        context["last_intent"] = "name"
        return f"Tanıştığımıza sevindim {name}. Bugün ne konuşmak istersin?", "name"

    if intent in {"yes", "no"}:
        previous_intent = context.get("last_intent", "")
        follow_up = FOLLOW_UPS.get(previous_intent, {}).get(intent)
        if follow_up:
            context["last_intent"] = previous_intent
            return follow_up, intent

    if intent == "why" and context.get("last_topic"):
        topic = context["last_topic"]
        return f"{topic} hakkında bunu söylememin nedeni sana daha iyi yardımcı olmak.", "why"

    if intent == "favorite":
        context["last_intent"] = intent
        return FAVORITES.get(contact.id, FAVORITES["asya"]), intent

    replies = CONTACT_REPLIES.get(contact.id, {}).get(intent) or COMMON_REPLIES.get(intent)
    if replies:
        context["last_intent"] = intent
        return replies[turn % len(replies)], intent

    topic = _topic_phrase(user_text)
    if topic:
        context["last_topic"] = topic
        context["last_intent"] = "bridge"
        return _topic_reply(contact.id, topic, turn), "bridge"

    context["last_intent"] = "bridge"
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


def _extract_name(value: str) -> str | None:
    match = re.search(r"\b(?:benim adım|benim adim|adım|adim|ismim)\s+([A-Za-zÇĞİÖŞÜçğıöşü]{2,20})", value, re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip().title()


def _topic_phrase(value: str) -> str:
    cleaned = re.sub(r"[.!?]+$", "", value.strip())
    cleaned = re.sub(r"^(bugün|bugun|az önce|az once|ben|bence)\s+", "", cleaned, flags=re.IGNORECASE)
    words = cleaned.split()
    if len(words) < 2:
        return ""
    return " ".join(words[:8])


def _topic_reply(contact_id: str, topic: str, turn: int) -> str:
    replies = {
        "asya": (
            f"{topic} demen ilgimi çekti. Bu sana nasıl hissettirdi?",
            f"{topic} hakkında seni dinliyorum. Sonra ne oldu?",
        ),
        "deniz": (
            f"{topic} ilginçmiş. Bunun en önemli kısmı sence ne?",
            f"{topic} konusunu anladım. Bir sonraki adım ne oldu?",
        ),
        "mira": (
            f"{topic} gerçekten ilginçmiş! En çok hangi kısmını sevdin?",
            f"{topic} deyince merak ettim. Sonra ne oldu?",
        ),
        "atlas": (
            f"{topic} konusunu anladım. Buradaki en önemli nokta nedir?",
            f"{topic} için ulaşmak istediğin sonuç nedir?",
        ),
        "zeynep": (
            f"{topic} hakkında anlattığını duydum. Bu sende nasıl bir his bıraktı?",
            f"{topic} gününün güzel bir parçası mıydı?",
        ),
        "kerem": (
            f"{topic} güzel bir anlatım oldu. Bunu bir cümle daha açıklayabilir misin?",
            f"{topic} konusunu başka kelimelerle nasıl anlatırsın?",
        ),
    }
    choices = replies.get(contact_id, replies["asya"])
    return choices[turn % len(choices)]
