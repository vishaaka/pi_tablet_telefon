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
        self.assertIn("kırmızı bir araba gördüm", reply)
        self.assertTrue(reply.endswith("?"))

    def test_follow_up_uses_previous_topic(self):
        context = {}
        scripted_reply(find_contact("mira", None), "Sıkıldım", context=context)
        reply, intent = scripted_reply(find_contact("mira", None), "Evet", context=context)
        self.assertEqual(intent, "yes")
        self.assertIn("Bilmece", reply)

    def test_remembers_users_name(self):
        context = {}
        reply, intent = scripted_reply(find_contact("asya", None), "Benim adım Ece", context=context)
        self.assertEqual(intent, "name")
        self.assertEqual(context["user_name"], "Ece")
        self.assertIn("Ece", reply)


if __name__ == "__main__":
    unittest.main()
