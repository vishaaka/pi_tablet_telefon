package com.vishaaka.pitablettelefon;

import android.app.Activity;
import android.graphics.Color;
import android.media.AudioManager;
import android.media.ToneGenerator;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Space;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class MainActivity extends Activity {
    private enum Screen {
        DIALER,
        CONTACTS,
        RINGING,
        IN_CALL
    }

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final List<Contact> contacts = new ArrayList<>();
    private LinearLayout root;
    private String dialedNumber = "";
    private Contact activeContact;
    private ToneGenerator toneGenerator;
    private int callSeconds = 0;
    private boolean muted = false;
    private boolean speaker = true;
    private boolean video = false;
    private Screen screen = Screen.DIALER;

    private final Runnable ringLoop = new Runnable() {
        @Override
        public void run() {
            if (screen != Screen.RINGING) {
                return;
            }
            if (toneGenerator != null) {
                toneGenerator.startTone(ToneGenerator.TONE_SUP_RINGTONE, 900);
            }
            handler.postDelayed(this, 2200);
        }
    };

    private final Runnable autoAnswer = new Runnable() {
        @Override
        public void run() {
            if (screen == Screen.RINGING) {
                showInCall();
            }
        }
    };

    private final Runnable callTimer = new Runnable() {
        @Override
        public void run() {
            if (screen != Screen.IN_CALL) {
                return;
            }
            callSeconds++;
            renderInCall();
            handler.postDelayed(this, 1000);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        seedContacts();
        showDialer();
    }

    @Override
    protected void onDestroy() {
        stopCallAudio();
        handler.removeCallbacksAndMessages(null);
        super.onDestroy();
    }

    private void seedContacts() {
        contacts.add(new Contact("Asya AI", "+90 532 101 10 10", "Sakin, net ve yardimci asistan", "Soft female", Color.rgb(61, 126, 255)));
        contacts.add(new Contact("Deniz AI", "+90 533 202 20 20", "Enerjik teknik destek", "Warm male", Color.rgb(24, 160, 88)));
        contacts.add(new Contact("Mira AI", "+90 534 303 30 30", "Goruntulu sohbet karakteri", "Bright female", Color.rgb(230, 180, 80)));
        contacts.add(new Contact("Atlas AI", "+90 535 404 40 40", "Ciddi is gorusmesi karakteri", "Deep male", Color.rgb(214, 69, 69)));
        contacts.add(new Contact("Zeynep AI", "+90 536 505 50 50", "Gunluk sohbet ve hatirlatma", "Calm female", Color.rgb(132, 94, 247)));
        contacts.add(new Contact("Kerem AI", "+90 537 606 60 60", "Yabanci dil pratik partneri", "Clear male", Color.rgb(0, 150, 136)));
    }

    private void resetRoot() {
        stopCallAudio();
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(16), dp(14), dp(16), dp(12));
        root.setBackgroundColor(color("bg"));
        setContentView(root);
    }

    private void addHeader(String title, String subtitle) {
        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.VERTICAL);
        header.setPadding(0, 0, 0, dp(12));

        TextView titleView = label(title, 28, color("text_primary"), true);
        TextView subtitleView = label(subtitle, 14, color("text_secondary"), false);

        header.addView(titleView);
        header.addView(subtitleView);
        root.addView(header);
    }

    private void addTabs() {
        LinearLayout tabs = new LinearLayout(this);
        tabs.setOrientation(LinearLayout.HORIZONTAL);
        tabs.setGravity(Gravity.CENTER);
        tabs.setPadding(0, 0, 0, dp(14));

        Button dialer = actionButton("Tus Takimi", screen == Screen.DIALER ? color("blue") : color("surface_2"));
        dialer.setOnClickListener(v -> showDialer());

        Button people = actionButton("Rehber", screen == Screen.CONTACTS ? color("blue") : color("surface_2"));
        people.setOnClickListener(v -> showContacts());

        tabs.addView(dialer, weightParams());
        addGap(tabs, 10, 1);
        tabs.addView(people, weightParams());
        root.addView(tabs);
    }

    private void showDialer() {
        screen = Screen.DIALER;
        resetRoot();
        addHeader("Pi Telefon", "AI kisilerle telefon simulasyonu");
        addTabs();
        renderDialer();
    }

    private void renderDialer() {
        TextView display = label(dialedNumber.isEmpty() ? "Numara girin" : dialedNumber, dialedNumber.isEmpty() ? 24 : 32, color("text_primary"), true);
        display.setGravity(Gravity.CENTER);
        display.setMinHeight(dp(62));
        root.addView(display);

        Contact match = findMatchingContact();
        if (match != null) {
            root.addView(contactPanel(match, "Eslesen kisi", true));
        } else {
            TextView helper = label("Numara yazdikca rehberdeki kayit otomatik gorunur.", 14, color("text_secondary"), false);
            helper.setGravity(Gravity.CENTER);
            root.addView(helper);
        }

        addGap(root, 1, 12);
        addKeypad();
        addDialerActions(match);
    }

    private void addKeypad() {
        String[][] rows = {
                {"1", "2", "3"},
                {"4", "5", "6"},
                {"7", "8", "9"},
                {"*", "0", "#"}
        };

        for (String[] row : rows) {
            LinearLayout line = new LinearLayout(this);
            line.setGravity(Gravity.CENTER);
            line.setPadding(0, dp(4), 0, dp(4));
            for (String key : row) {
                Button button = roundButton(key, 26, color("surface_2"));
                button.setOnClickListener(v -> {
                    dialedNumber += key;
                    showDialer();
                });
                line.addView(button, keypadParams());
            }
            root.addView(line);
        }
    }

    private void addDialerActions(Contact match) {
        LinearLayout actions = new LinearLayout(this);
        actions.setGravity(Gravity.CENTER);
        actions.setPadding(0, dp(10), 0, 0);

        Button delete = roundButton("Sil", 18, color("surface_2"));
        delete.setOnClickListener(v -> {
            if (!dialedNumber.isEmpty()) {
                dialedNumber = dialedNumber.substring(0, dialedNumber.length() - 1);
            }
            showDialer();
        });
        delete.setOnLongClickListener(v -> {
            dialedNumber = "";
            showDialer();
            return true;
        });

        Button call = roundButton("Ara", 20, color("green"));
        call.setOnClickListener(v -> {
            Contact target = match != null ? match : new Contact("Bilinmeyen Numara", dialedNumber, "Gecici AI arama simulasyonu", "Default", Color.rgb(61, 126, 255));
            if (!target.phone.isEmpty()) {
                startOutgoingCall(target);
            }
        });

        Button contactsButton = roundButton("Rehber", 18, color("surface_2"));
        contactsButton.setOnClickListener(v -> showContacts());

        actions.addView(delete, keypadParams());
        actions.addView(call, keypadParams());
        actions.addView(contactsButton, keypadParams());
        root.addView(actions);
    }

    private void showContacts() {
        screen = Screen.CONTACTS;
        resetRoot();
        addHeader("Rehber", "Temsili numaralar secilebilir");
        addTabs();

        ScrollView scrollView = new ScrollView(this);
        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        scrollView.addView(list);

        for (Contact contact : contacts) {
            list.addView(contactPanel(contact, contact.voice, true));
            addGap(list, 1, 10);
        }

        root.addView(scrollView, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));
    }

    private View contactPanel(Contact contact, String caption, boolean callable) {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.HORIZONTAL);
        panel.setGravity(Gravity.CENTER_VERTICAL);
        panel.setPadding(dp(12), dp(12), dp(12), dp(12));
        panel.setBackgroundResource(R.drawable.panel);

        TextView avatar = label(contact.initials(), 22, Color.WHITE, true);
        avatar.setGravity(Gravity.CENTER);
        avatar.setBackgroundColor(contact.color);
        panel.addView(avatar, new LinearLayout.LayoutParams(dp(58), dp(58)));
        addGap(panel, 12, 1);

        LinearLayout text = new LinearLayout(this);
        text.setOrientation(LinearLayout.VERTICAL);
        text.addView(label(contact.name, 18, color("text_primary"), true));
        text.addView(label(contact.phone, 15, color("text_secondary"), false));
        text.addView(label(caption + " - " + contact.persona, 12, color("text_secondary"), false));
        panel.addView(text, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));

        if (callable) {
            Button call = actionButton("Ara", color("green"));
            call.setOnClickListener(v -> startOutgoingCall(contact));
            panel.addView(call, new LinearLayout.LayoutParams(dp(74), dp(44)));
        }
        return panel;
    }

    private Contact findMatchingContact() {
        String digits = dialedNumber.replaceAll("\\D+", "");
        if (digits.length() < 2) {
            return null;
        }
        for (Contact contact : contacts) {
            String contactDigits = contact.digits();
            if (contactDigits.contains(digits) || contactDigits.endsWith(digits)) {
                return contact;
            }
        }
        return null;
    }

    private void startOutgoingCall(Contact contact) {
        activeContact = contact;
        callSeconds = 0;
        muted = false;
        speaker = true;
        video = false;
        screen = Screen.RINGING;
        renderRinging("Araniyor", "Baglanti hazirlaniyor...");
        startRingAudio();
        handler.postDelayed(() -> {
            if (screen == Screen.RINGING) {
                renderRinging("Caliyor", "AI kisi cevap bekliyor...");
            }
        }, 1400);
        handler.postDelayed(autoAnswer, 5200);
    }

    private void renderRinging(String state, String detail) {
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(dp(18), dp(18), dp(18), dp(18));
        root.setBackgroundColor(color("bg"));
        setContentView(root);

        TextView status = label(state, 24, color("text_secondary"), false);
        status.setGravity(Gravity.CENTER);
        root.addView(status);

        addGap(root, 1, 24);
        root.addView(callAvatar(activeContact, 136));
        addGap(root, 1, 18);

        TextView name = label(activeContact.name, 30, color("text_primary"), true);
        name.setGravity(Gravity.CENTER);
        root.addView(name);

        TextView number = label(activeContact.phone, 18, color("text_secondary"), false);
        number.setGravity(Gravity.CENTER);
        root.addView(number);

        TextView detailView = label(detail, 15, color("yellow"), false);
        detailView.setGravity(Gravity.CENTER);
        root.addView(detailView);

        Space spacer = new Space(this);
        root.addView(spacer, new LinearLayout.LayoutParams(1, 0, 1));

        Button end = roundButton("Kapat", 20, color("red"));
        end.setOnClickListener(v -> endCall());
        root.addView(end, new LinearLayout.LayoutParams(dp(128), dp(64)));
    }

    private void showInCall() {
        screen = Screen.IN_CALL;
        stopCallAudio();
        renderInCall();
        handler.postDelayed(callTimer, 1000);
    }

    private void renderInCall() {
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(dp(16), dp(16), dp(16), dp(12));
        root.setBackgroundColor(video ? Color.rgb(18, 24, 33) : color("bg"));
        setContentView(root);

        TextView status = label(video ? "Goruntulu arama simulasyonu" : "Sesli arama simulasyonu", 16, color("text_secondary"), false);
        status.setGravity(Gravity.CENTER);
        root.addView(status);

        addGap(root, 1, 16);
        root.addView(callAvatar(activeContact, video ? 180 : 132));
        addGap(root, 1, 12);

        TextView name = label(activeContact.name, 30, color("text_primary"), true);
        name.setGravity(Gravity.CENTER);
        root.addView(name);

        TextView timer = label(formatTime(callSeconds), 22, color("green"), true);
        timer.setGravity(Gravity.CENTER);
        root.addView(timer);

        TextView aiLine = label("AI persona: " + activeContact.persona, 14, color("text_secondary"), false);
        aiLine.setGravity(Gravity.CENTER);
        root.addView(aiLine);

        Space spacer = new Space(this);
        root.addView(spacer, new LinearLayout.LayoutParams(1, 0, 1));

        addCallControls();
    }

    private void addCallControls() {
        LinearLayout rowOne = new LinearLayout(this);
        rowOne.setGravity(Gravity.CENTER);
        rowOne.addView(controlButton(muted ? "Mik. Ac" : "Sessiz", () -> {
            muted = !muted;
            renderInCall();
        }));
        rowOne.addView(controlButton(speaker ? "Ahize" : "Hoparlor", () -> {
            speaker = !speaker;
            renderInCall();
        }));
        rowOne.addView(controlButton(video ? "Video Kapat" : "Video", () -> {
            video = !video;
            renderInCall();
        }));
        root.addView(rowOne);

        LinearLayout rowTwo = new LinearLayout(this);
        rowTwo.setGravity(Gravity.CENTER);
        rowTwo.setPadding(0, dp(10), 0, 0);

        Button keypad = roundButton("Tuslar", 17, color("surface_2"));
        keypad.setOnClickListener(v -> {
            dialedNumber = "";
            showDialer();
        });

        Button end = roundButton("Kapat", 20, color("red"));
        end.setOnClickListener(v -> endCall());

        rowTwo.addView(keypad, keypadParams());
        rowTwo.addView(end, keypadParams());
        root.addView(rowTwo);
    }

    private View controlButton(String text, Runnable action) {
        Button button = roundButton(text, 15, color("surface_2"));
        button.setOnClickListener(v -> action.run());
        return button;
    }

    private TextView callAvatar(Contact contact, int sizeDp) {
        TextView avatar = label(contact.initials(), sizeDp > 150 ? 62 : 48, Color.WHITE, true);
        avatar.setGravity(Gravity.CENTER);
        avatar.setBackgroundColor(contact.color);
        avatar.setMinWidth(dp(sizeDp));
        avatar.setMinHeight(dp(sizeDp));
        return avatar;
    }

    private void endCall() {
        stopCallAudio();
        handler.removeCallbacks(autoAnswer);
        handler.removeCallbacks(callTimer);
        dialedNumber = "";
        screen = Screen.DIALER;
        resetRoot();
        addHeader("Arama bitti", activeContact != null ? activeContact.name + " ile gorusme kapandi" : "Gorusme kapandi");
        Button back = actionButton("Tus Takimina Don", color("green"));
        back.setOnClickListener(v -> showDialer());
        root.addView(back, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(54)));
        addGap(root, 1, 12);
        Button people = actionButton("Rehberi Ac", color("surface_2"));
        people.setOnClickListener(v -> showContacts());
        root.addView(people, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(54)));
    }

    private void startRingAudio() {
        stopCallAudio();
        toneGenerator = new ToneGenerator(AudioManager.STREAM_VOICE_CALL, 70);
        handler.post(ringLoop);
    }

    private void stopCallAudio() {
        handler.removeCallbacks(ringLoop);
        if (toneGenerator != null) {
            toneGenerator.release();
            toneGenerator = null;
        }
    }

    private Button actionButton(String text, int backgroundColor) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(Color.WHITE);
        button.setTextSize(14);
        button.setAllCaps(false);
        button.setBackgroundColor(backgroundColor);
        return button;
    }

    private Button roundButton(String text, int textSize, int backgroundColor) {
        Button button = actionButton(text, backgroundColor);
        button.setTextSize(textSize);
        return button;
    }

    private TextView label(String text, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextSize(size);
        view.setTextColor(color);
        view.setIncludeFontPadding(true);
        if (bold) {
            view.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        }
        return view;
    }

    private LinearLayout.LayoutParams weightParams() {
        return new LinearLayout.LayoutParams(0, dp(48), 1);
    }

    private LinearLayout.LayoutParams keypadParams() {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, dp(62), 1);
        params.setMargins(dp(5), 0, dp(5), 0);
        return params;
    }

    private void addGap(LinearLayout layout, int widthDp, int heightDp) {
        Space space = new Space(this);
        layout.addView(space, new LinearLayout.LayoutParams(dp(widthDp), dp(heightDp)));
    }

    private String formatTime(int totalSeconds) {
        int minutes = totalSeconds / 60;
        int seconds = totalSeconds % 60;
        return String.format(Locale.US, "%02d:%02d", minutes, seconds);
    }

    private int color(String name) {
        switch (name) {
            case "bg":
                return Color.rgb(16, 20, 24);
            case "surface_2":
                return Color.rgb(32, 40, 50);
            case "text_primary":
                return Color.rgb(245, 247, 250);
            case "text_secondary":
                return Color.rgb(168, 179, 194);
            case "green":
                return Color.rgb(24, 160, 88);
            case "red":
                return Color.rgb(214, 69, 69);
            case "blue":
                return Color.rgb(61, 126, 255);
            case "yellow":
                return Color.rgb(230, 180, 80);
            default:
                return Color.WHITE;
        }
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }
}
