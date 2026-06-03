from .models import Contact


CONTACTS = [
    Contact(
        id="asya",
        name="Asya AI",
        phone="+90 532 101 10 10",
        persona="Sakin, net ve yardimci asistan",
        voice="soft_female",
    ),
    Contact(
        id="deniz",
        name="Deniz AI",
        phone="+90 533 202 20 20",
        persona="Enerjik teknik destek",
        voice="warm_male",
    ),
    Contact(
        id="mira",
        name="Mira AI",
        phone="+90 534 303 30 30",
        persona="Goruntulu sohbet karakteri",
        voice="bright_female",
    ),
    Contact(
        id="atlas",
        name="Atlas AI",
        phone="+90 535 404 40 40",
        persona="Ciddi is gorusmesi karakteri",
        voice="deep_male",
    ),
    Contact(
        id="zeynep",
        name="Zeynep AI",
        phone="+90 536 505 50 50",
        persona="Gunluk sohbet ve hatirlatma",
        voice="calm_female",
    ),
    Contact(
        id="kerem",
        name="Kerem AI",
        phone="+90 537 606 60 60",
        persona="Yabanci dil pratik partneri",
        voice="clear_male",
    ),
]


def digits(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def find_contact(contact_id: str | None, phone: str | None) -> Contact:
    if contact_id:
        for contact in CONTACTS:
            if contact.id == contact_id:
                return contact

    if phone:
        phone_digits = digits(phone)
        for contact in CONTACTS:
            contact_digits = digits(contact.phone)
            if phone_digits and (phone_digits in contact_digits or contact_digits.endswith(phone_digits)):
                return contact

    return Contact(
        id="unknown",
        name="Bilinmeyen Numara",
        phone=phone or "000",
        persona="Gecici AI arama simulasyonu",
        voice="default",
        video_enabled=False,
    )
