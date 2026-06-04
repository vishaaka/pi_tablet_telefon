package com.vishaaka.pitablettelefon;

final class Contact {
    final String id;
    final String name;
    final String phone;
    final String persona;
    final String voice;
    final int color;

    Contact(String id, String name, String phone, String persona, String voice, int color) {
        this.id = id;
        this.name = name;
        this.phone = phone;
        this.persona = persona;
        this.voice = voice;
        this.color = color;
    }

    Contact(String name, String phone, String persona, String voice, int color) {
        this("unknown", name, phone, persona, voice, color);
    }

    String initials() {
        String[] parts = name.trim().split("\\s+");
        if (parts.length == 0 || parts[0].isEmpty()) {
            return "?";
        }
        if (parts.length == 1) {
            return parts[0].substring(0, 1).toUpperCase();
        }
        return (parts[0].substring(0, 1) + parts[parts.length - 1].substring(0, 1)).toUpperCase();
    }

    String digits() {
        return phone.replaceAll("\\D+", "");
    }
}
