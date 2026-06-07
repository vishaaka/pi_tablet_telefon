import unittest

from app.fast_chat import scripted_reply
from app.personas import find_contact


class FastChatTests(unittest.TestCase):
    def test_turkish_greeting_matches(self):
        reply, intent = scripted_reply(find_contact("asya", None), "Merhaba, nasılsın?")
        self.assertEqual(intent, "greeting")
        self.assertIn("Asya", reply)

    def test_contact_specific_technical_reply(self):
        reply, intent = scripted_reply(find_contact("deniz", None), "Telefon çalışmıyor")
        self.assertEqual(intent, "technical")
        self.assertIn("bağlantıları", reply)

    def test_unknown_message_gets_conversational_bridge(self):
        reply, intent = scripted_reply(find_contact("mira", None), "Bugün kırmızı bir araba gördüm")
        self.assertEqual(intent, "bridge")
        self.assertTrue(reply.endswith("?"))


if __name__ == "__main__":
    unittest.main()
