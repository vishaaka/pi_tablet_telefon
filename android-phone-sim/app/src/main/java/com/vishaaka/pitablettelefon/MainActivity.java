package com.vishaaka.pitablettelefon;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.media.ToneGenerator;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
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
        RECENTS,
        CONTACTS,
        RINGING,
        IN_CALL
    }

    private static final int BG = Color.rgb(248, 247, 250);
    private static final int PANEL = Color.WHITE;
    private static final int TEXT = Color.rgb(18, 18, 20);
    private static final int MUTED = Color.rgb(128, 128, 138);
    private static final int LINE = Color.rgb(224, 224, 230);
    private static final int GREEN = Color.rgb(21, 171, 96);

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final List<Contact> contacts = new ArrayList<>();
    private final List<RecentCall> recentCalls = new ArrayList<>();
    private final BackendClient backendClient = new BackendClient();

    private LinearLayout root;
    private String dialedNumber = "";
    private Contact activeContact;
    private String activeCallId = "";
    private String activeAiReply = "";
    private String backendStatus = "";
    private ToneGenerator toneGenerator;
    private ToneGenerator keyToneGenerator;
    private MediaPlayer mediaPlayer;
    private int callSeconds = 0;
    private boolean muted = false;
    private boolean speaker = true;
    private boolean video = false;
    private boolean initialGreetingRequested = false;
    private boolean pendingInitialGreeting = false;
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
        configureWindow();
        setVolumeControlStream(AudioManager.STREAM_MUSIC);
        boostAppAudio();
        seedContacts();
        seedRecentCalls();
        showDialer();
        refreshContactsFromBackend();
    }

    @Override
    protected void onResume() {
        super.onResume();
        boostAppAudio();
    }

    @Override
    protected void onDestroy() {
        stopCallAudio();
        stopTtsAudio();
        stopKeyAudio();
        handler.removeCallbacksAndMessages(null);
        super.onDestroy();
    }

    private void configureWindow() {
        Window window = getWindow();
        window.setStatusBarColor(BG);
        window.setNavigationBarColor(BG);
        window.getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
        );
    }

    private void boostAppAudio() {
        AudioManager audioManager = (AudioManager) getSystemService(AUDIO_SERVICE);
        if (audioManager == null) {
            return;
        }
        int[] streams = {
                AudioManager.STREAM_MUSIC,
                AudioManager.STREAM_RING,
                AudioManager.STREAM_VOICE_CALL
        };
        for (int stream : streams) {
            try {
                audioManager.setStreamMute(stream, false);
                audioManager.setStreamVolume(stream, audioManager.getStreamMaxVolume(stream), 0);
            } catch (Exception ignored) {
            }
        }
    }

    private void seedContacts() {
        contacts.clear();
        contacts.add(new Contact("asya", "Asya AI", "+90 532 101 10 10", "Sakin, net ve yardimci asistan", "Soft female", Color.rgb(134, 160, 225)));
        contacts.add(new Contact("deniz", "Deniz AI", "+90 533 202 20 20", "Enerjik teknik destek", "Warm male", Color.rgb(225, 210, 102)));
        contacts.add(new Contact("mira", "Mira AI", "+90 534 303 30 30", "Goruntulu sohbet karakteri", "Bright female", Color.rgb(226, 124, 180)));
        contacts.add(new Contact("atlas", "Atlas AI", "+90 535 404 40 40", "Ciddi is gorusmesi karakteri", "Deep male", Color.rgb(100, 190, 210)));
        contacts.add(new Contact("zeynep", "Zeynep AI", "+90 536 505 50 50", "Gunluk sohbet ve hatirlatma", "Calm female", Color.rgb(117, 200, 184)));
        contacts.add(new Contact("kerem", "Kerem AI", "+90 537 606 60 60", "Yabanci dil pratik partneri", "Clear male", Color.rgb(255, 161, 127)));
    }

    private void seedRecentCalls() {
        recentCalls.clear();
        recentCalls.add(new RecentCall("444 5 375", "Dün", "19:36", true));
        recentCalls.add(new RecentCall("Dilek (2)", "Dün", "18:27", false));
        recentCalls.add(new RecentCall("444 6 891", "Dün", "15:58", false));
        recentCalls.add(new RecentCall("+90 536 417 09 75", "Dün", "15:47", false));
        recentCalls.add(new RecentCall("Dilek", "3 Haziran Çarşamba", "18:57", true));
        recentCalls.add(new RecentCall("Asya AI", "3 Haziran Çarşamba", "17:20", true));
    }

    private void refreshContactsFromBackend() {
        backendClient.fetchContacts(new BackendClient.ContactsCallback() {
            @Override
            public void onResult(List<Contact> remoteContacts, String baseUrl) {
                handler.post(() -> {
                    contacts.clear();
                    contacts.addAll(remoteContacts);
                    backendStatus = baseUrl;
                    if (screen == Screen.CONTACTS) {
                        showContacts();
                    }
                });
            }

            @Override
            public void onError(String message) {
                handler.post(() -> backendStatus = "");
            }
        });
    }

    private void resetRoot(boolean withBottomNav) {
        stopCallAudio();
        LinearLayout shell = new LinearLayout(this);
        shell.setOrientation(LinearLayout.VERTICAL);
        shell.setBackgroundColor(BG);
        setContentView(shell);

        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(14), dp(screen == Screen.DIALER && isCompactDialer() ? 4 : 18), dp(14), 0);
        shell.addView(content, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));
        root = content;

        if (withBottomNav) {
            addBottomNav(shell);
        }
    }

    private void showDialer() {
        screen = Screen.DIALER;
        resetRoot(true);
        addTopActions(false, false);

        Contact match = findMatchingContact();
        addDialSuggestion(match);
        addDialDisplay(match);

        addKeypad();
        addDialerCallButton(match);

        Space bottomSpace = new Space(this);
        root.addView(bottomSpace, new LinearLayout.LayoutParams(1, dp(isCompactDialer() ? 0 : 10)));
    }

    private void addDialSuggestion(Contact match) {
        LinearLayout slot = new LinearLayout(this);
        slot.setOrientation(LinearLayout.VERTICAL);
        slot.setGravity(isCompactDialer() ? Gravity.BOTTOM : Gravity.CENTER_VERTICAL);

        if (!dialedNumber.isEmpty() && match != null) {
            LinearLayout row = new LinearLayout(this);
            row.setGravity(Gravity.CENTER_VERTICAL);
            row.setPadding(dp(8), 0, dp(8), 0);
            row.setBackground(round(PANEL, dp(18)));
            row.setOnClickListener(v -> startOutgoingCall(match));

            TextView avatar = avatar(match.initials().substring(0, 1), match.color);
            row.addView(avatar, square(dp(isCompactDialer() ? 32 : 42)));

            LinearLayout textBlock = new LinearLayout(this);
            textBlock.setOrientation(LinearLayout.VERTICAL);
            textBlock.setPadding(dp(10), 0, 0, 0);

            TextView name = text(match.name, isCompactDialer() ? 13 : 16, TEXT, false);
            TextView phone = text(match.phone, isCompactDialer() ? 10 : 12, MUTED, false);
            textBlock.addView(name, fullWidth(dp(isCompactDialer() ? 20 : 24)));
            textBlock.addView(phone, fullWidth(dp(isCompactDialer() ? 16 : 18)));
            row.addView(textBlock, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));

            TextView callMini = text("", 1, Color.WHITE, false);
            callMini.setGravity(Gravity.CENTER);
            callMini.setBackground(round(GREEN, dp(40)));
            setPhoneIcon(callMini, isCompactDialer() ? 20 : 22);
            row.addView(callMini, square(dp(isCompactDialer() ? 36 : 42)));

            LinearLayout.LayoutParams rowParams = fullWidth(dp(isCompactDialer() ? 44 : 58));
            rowParams.setMargins(0, 0, 0, dp(isCompactDialer() ? 2 : 8));
            slot.addView(row, rowParams);
        }

        root.addView(slot, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1
        ));
    }

    private void addDialDisplay(Contact match) {
        boolean compact = isCompactDialer();
        LinearLayout display = new LinearLayout(this);
        display.setOrientation(LinearLayout.VERTICAL);
        display.setGravity(Gravity.CENTER);

        TextView number = text(dialedNumber, compact ? 23 : 34, TEXT, true);
        number.setGravity(Gravity.CENTER);
        TextView name = text(match != null && dialedNumber.isEmpty() ? match.name : "", compact ? 10 : 14, GREEN, false);
        name.setGravity(Gravity.CENTER);

        display.addView(number, fullWidth(dp(compact ? 30 : 46)));
        display.addView(name, fullWidth(dp(compact ? 16 : 24)));
        root.addView(display, fullWidth(dp(compact ? 48 : 76)));
    }

    private void addTopActions(boolean showTitle, boolean contactsMode) {
        boolean compactDialer = !showTitle && isCompactDialer();
        int barHeight = compactDialer ? 42 : 62;
        int itemHeight = compactDialer ? 36 : 54;
        int iconSize = compactDialer ? 36 : 44;

        LinearLayout bar = new LinearLayout(this);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(0, 0, 0, dp(compactDialer ? 0 : 8));

        if (showTitle) {
            TextView title = text("Telefon", contactsMode ? 22 : 30, TEXT, true);
            title.setGravity(contactsMode ? Gravity.START : Gravity.CENTER);
            bar.addView(title, new LinearLayout.LayoutParams(0, dp(itemHeight), 1));
        } else {
            Space space = new Space(this);
            bar.addView(space, new LinearLayout.LayoutParams(0, dp(itemHeight), 1));
        }

        if (contactsMode) {
            bar.addView(iconButton("+", 30, v -> {
            }), square(dp(44)));
        }
        bar.addView(iconButton("⌕", 28, v -> {
        }), square(dp(iconSize)));
        bar.addView(iconButton("⋮", 26, v -> {
        }), square(dp(compactDialer ? 30 : 34)));
        root.addView(bar, fullWidth(dp(barHeight)));
    }

    private void addKeypad() {
        String[][] keys = {
                {"1", ""},
                {"2", "ABC"},
                {"3", "DEF"},
                {"4", "GHI"},
                {"5", "JKL"},
                {"6", "MNO"},
                {"7", "PQRS"},
                {"8", "TUV"},
                {"9", "WXYZ"},
                {"*", ""},
                {"0", "+"},
                {"#", ""}
        };

        for (int row = 0; row < 4; row++) {
            LinearLayout line = new LinearLayout(this);
            line.setGravity(Gravity.CENTER);
            for (int col = 0; col < 3; col++) {
                String[] key = keys[row * 3 + col];
                line.addView(keyView(key[0], key[1]), new LinearLayout.LayoutParams(0, dp(dialerKeyHeight()), 1));
            }
            root.addView(line, fullWidth(dp(dialerKeyHeight())));
        }
    }

    private View keyView(String digit, String letters) {
        boolean compact = isCompactDialer();
        LinearLayout key = new LinearLayout(this);
        key.setOrientation(LinearLayout.VERTICAL);
        key.setGravity(Gravity.CENTER);
        key.setOnClickListener(v -> {
            dialedNumber += digit;
            playKeyTone(digit);
            showDialer();
        });
        key.setOnLongClickListener(v -> {
            if ("0".equals(digit)) {
                dialedNumber += "+";
                showDialer();
                return true;
            }
            return false;
        });

        TextView number = text(digit, compact ? 26 : 34, Color.BLACK, false);
        number.setGravity(Gravity.CENTER);
        TextView sub = text(letters, compact ? 9 : 11, MUTED, false);
        sub.setGravity(Gravity.CENTER);
        key.addView(number, fullWidth(dp(compact ? 29 : 38)));
        key.addView(sub, fullWidth(dp(compact ? 14 : 18)));
        return key;
    }

    private void addDialerCallButton(Contact match) {
        boolean compact = isCompactDialer();
        int buttonSize = compact ? 50 : 64;
        LinearLayout line = new LinearLayout(this);
        line.setGravity(Gravity.CENTER);
        line.setPadding(0, dp(compact ? 2 : 8), 0, 0);

        TextView video = text(dialedNumber.isEmpty() ? "" : "▣", compact ? 22 : 26, GREEN, true);
        video.setGravity(Gravity.CENTER);
        line.addView(video, square(dp(buttonSize)));

        TextView call = text("", 1, Color.WHITE, true);
        call.setGravity(Gravity.CENTER);
        call.setBackground(round(GREEN, dp(buttonSize)));
        setPhoneIcon(call, compact ? 30 : 34);
        call.setOnClickListener(v -> {
            Contact target = match != null ? match : new Contact("unknown", "Bilinmeyen Numara", dialedNumber, "Geçici AI arama simülasyonu", "Default", Color.rgb(134, 160, 225));
            if (!target.phone.isEmpty()) {
                startOutgoingCall(target);
            }
        });
        LinearLayout.LayoutParams callParams = square(dp(buttonSize));
        callParams.setMargins(dp(compact ? 16 : 26), 0, dp(compact ? 16 : 26), 0);
        line.addView(call, callParams);

        TextView delete = text("", compact ? 20 : 24, MUTED, false);
        delete.setGravity(Gravity.CENTER);
        if (!dialedNumber.isEmpty()) {
            delete.setText("⌫");
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
        }
        line.addView(delete, square(dp(buttonSize)));

        root.addView(line, fullWidth(dp(compact ? 58 : 82)));
    }

    private void showRecents() {
        screen = Screen.RECENTS;
        resetRoot(true);
        addTopActions(true, false);

        ScrollView scroll = new ScrollView(this);
        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        list.setPadding(0, dp(80), 0, 0);
        scroll.addView(list);

        String currentGroup = "";
        for (RecentCall call : recentCalls) {
            if (!currentGroup.equals(call.group)) {
                currentGroup = call.group;
                TextView group = text(currentGroup, 13, MUTED, true);
                group.setPadding(0, dp(12), 0, dp(8));
                list.addView(group, fullWidth(dp(36)));
            }
            list.addView(recentRow(call), fullWidth(dp(58)));
        }
        root.addView(scroll, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));
    }

    private View recentRow(RecentCall call) {
        LinearLayout row = new LinearLayout(this);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(0, 0, 0, 0);

        TextView icon = text(call.outgoing ? "↗" : "↙", 20, call.outgoing ? GREEN : MUTED, true);
        icon.setGravity(Gravity.CENTER);
        row.addView(icon, square(dp(36)));

        TextView name = text(call.label, 17, TEXT, false);
        row.addView(name, new LinearLayout.LayoutParams(0, dp(58), 1));

        TextView time = text(call.time, 13, MUTED, false);
        time.setGravity(Gravity.CENTER_VERTICAL | Gravity.END);
        row.addView(time, new LinearLayout.LayoutParams(dp(52), dp(58)));
        row.setOnClickListener(v -> startOutgoingCall(contactForLabel(call.label)));
        return row;
    }

    private void showContacts() {
        screen = Screen.CONTACTS;
        resetRoot(true);
        addTopActions(true, true);

        ScrollView scroll = new ScrollView(this);
        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(list);

        TextView profileLabel = text("Profilim", 13, MUTED, true);
        profileLabel.setPadding(0, 0, 0, dp(6));
        list.addView(profileLabel, fullWidth(dp(30)));
        list.addView(profileRow(), fullWidth(dp(58)));

        TextView favorites = text("★  Favorilerim", 14, MUTED, true);
        favorites.setPadding(dp(8), dp(12), 0, dp(6));
        list.addView(favorites, fullWidth(dp(48)));

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackground(round(PANEL, dp(18)));
        card.setPadding(0, dp(6), 0, dp(6));
        for (Contact contact : contacts) {
            card.addView(contactRow(contact), fullWidth(dp(58)));
        }
        list.addView(card, fullWidth(LinearLayout.LayoutParams.WRAP_CONTENT));
        root.addView(scroll, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));
    }

    private View profileRow() {
        LinearLayout row = new LinearLayout(this);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(12), 0, dp(14), 0);
        row.setBackground(round(PANEL, dp(18)));
        TextView avatar = avatar("●", Color.rgb(142, 164, 228));
        row.addView(avatar, square(dp(42)));
        TextView name = text("Erbil Zengin", 17, TEXT, false);
        name.setPadding(dp(12), 0, 0, 0);
        row.addView(name, new LinearLayout.LayoutParams(0, dp(58), 1));
        return row;
    }

    private View contactRow(Contact contact) {
        LinearLayout row = new LinearLayout(this);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(12), 0, dp(14), 0);
        row.setOnClickListener(v -> startOutgoingCall(contact));

        TextView avatar = avatar(contact.initials().substring(0, 1), contact.color);
        row.addView(avatar, square(dp(42)));

        TextView name = text(contact.name, 17, TEXT, false);
        name.setPadding(dp(12), 0, 0, 0);
        row.addView(name, new LinearLayout.LayoutParams(0, dp(58), 1));
        return row;
    }

    private void addBottomNav(LinearLayout shell) {
        LinearLayout nav = new LinearLayout(this);
        nav.setGravity(Gravity.CENTER);
        boolean compact = screen == Screen.DIALER && isCompactDialer();
        nav.setPadding(0, dp(compact ? 0 : 4), 0, dp(compact ? 0 : 4));
        nav.setBackgroundColor(BG);
        shell.addView(nav, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(compact ? 54 : 70)));

        nav.addView(navItem("⠿", "Klavye", screen == Screen.DIALER, v -> showDialer()), new LinearLayout.LayoutParams(0, dp(compact ? 52 : 62), 1));
        nav.addView(navItem("☏", "Son aramalar", screen == Screen.RECENTS, v -> showRecents()), new LinearLayout.LayoutParams(0, dp(compact ? 52 : 62), 1));
        nav.addView(navItem("♙", "Kişiler", screen == Screen.CONTACTS, v -> showContacts()), new LinearLayout.LayoutParams(0, dp(compact ? 52 : 62), 1));
    }

    private View navItem(String icon, String label, boolean selected, View.OnClickListener listener) {
        LinearLayout item = new LinearLayout(this);
        item.setOrientation(LinearLayout.VERTICAL);
        item.setGravity(Gravity.CENTER);
        item.setOnClickListener(listener);
        int color = selected ? Color.BLACK : MUTED;

        TextView iconView = text(icon, 22, color, selected);
        iconView.setGravity(Gravity.CENTER);
        TextView labelView = text(label, isCompactDialer() && screen == Screen.DIALER ? 10 : 12, color, selected);
        labelView.setGravity(Gravity.CENTER);
        item.addView(iconView, fullWidth(dp(isCompactDialer() && screen == Screen.DIALER ? 24 : 28)));
        item.addView(labelView, fullWidth(dp(isCompactDialer() && screen == Screen.DIALER ? 20 : 24)));
        return item;
    }

    private void startOutgoingCall(Contact contact) {
        activeContact = contact;
        activeCallId = "";
        activeAiReply = "";
        callSeconds = 0;
        muted = false;
        speaker = true;
        video = false;
        initialGreetingRequested = false;
        pendingInitialGreeting = false;
        screen = Screen.RINGING;
        renderRinging("Aranıyor", "Bağlantı hazırlanıyor...");

        backendClient.startCall(contact, "voice", new BackendClient.CallCallback() {
            @Override
            public void onResult(String callId, String baseUrl) {
                handler.post(() -> {
                    activeCallId = callId;
                    backendStatus = baseUrl;
                    if (screen == Screen.RINGING) {
                        renderRinging("Çalıyor", "AI oturumu açıldı");
                    } else if (screen == Screen.IN_CALL && pendingInitialGreeting) {
                        requestInitialGreeting();
                    }
                });
            }

            @Override
            public void onError(String message) {
                handler.post(() -> {
                    activeCallId = "";
                    backendStatus = message;
                    if (screen == Screen.RINGING) {
                        renderRinging("Backend yok", shortStatus(message));
                    }
                });
            }
        });

        startRingAudio();
        handler.postDelayed(() -> {
            if (screen == Screen.RINGING) {
                renderRinging(
                        activeCallId.isEmpty() ? "Backend bekleniyor" : "Çalıyor",
                        activeCallId.isEmpty() ? shortStatus(backendStatus.isEmpty() ? "AI oturumu bekleniyor" : backendStatus) : "AI oturumu hazır"
                );
            }
        }, 1400);
        handler.postDelayed(autoAnswer, 5200);
    }

    private void renderRinging(String state, String detail) {
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(dp(18), dp(18), dp(18), dp(26));
        root.setBackgroundColor(BG);
        setContentView(root);

        root.addView(text(state, 24, MUTED, false), fullWidth(dp(44)));
        TextView avatar = avatar(activeContact.initials(), activeContact.color);
        avatar.setTextSize(42);
        root.addView(avatar, square(dp(118)));

        TextView name = text(activeContact.name, 30, TEXT, true);
        name.setGravity(Gravity.CENTER);
        root.addView(name, fullWidth(dp(54)));

        TextView number = text(activeContact.phone, 17, MUTED, false);
        number.setGravity(Gravity.CENTER);
        root.addView(number, fullWidth(dp(34)));

        TextView info = text(detail, 14, MUTED, false);
        info.setGravity(Gravity.CENTER);
        root.addView(info, fullWidth(dp(32)));

        Space spacer = new Space(this);
        root.addView(spacer, new LinearLayout.LayoutParams(1, 0, 1));

        TextView end = text("Kapat", 18, Color.WHITE, true);
        end.setGravity(Gravity.CENTER);
        end.setBackground(round(Color.rgb(220, 70, 70), dp(64)));
        end.setOnClickListener(v -> endCall());
        root.addView(end, new LinearLayout.LayoutParams(dp(128), dp(64)));
    }

    private void showInCall() {
        screen = Screen.IN_CALL;
        stopCallAudio();
        renderInCall();
        requestInitialGreeting();
        handler.postDelayed(callTimer, 1000);
    }

    private void renderInCall() {
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(dp(16), dp(18), dp(16), dp(26));
        root.setBackgroundColor(video ? Color.rgb(30, 34, 40) : BG);
        setContentView(root);

        int mainText = video ? Color.WHITE : TEXT;
        int subText = video ? Color.rgb(190, 196, 205) : MUTED;
        TextView status = text(video ? "Görüntülü arama" : "Sesli arama", 16, subText, false);
        status.setGravity(Gravity.CENTER);
        root.addView(status, fullWidth(dp(44)));

        TextView avatar = avatar(activeContact.initials(), activeContact.color);
        avatar.setTextSize(video ? 56 : 44);
        root.addView(avatar, square(video ? dp(160) : dp(120)));

        TextView name = text(activeContact.name, 30, mainText, true);
        name.setGravity(Gravity.CENTER);
        root.addView(name, fullWidth(dp(52)));

        TextView timer = text(formatTime(callSeconds), 22, GREEN, true);
        timer.setGravity(Gravity.CENTER);
        root.addView(timer, fullWidth(dp(44)));

        String aiText = activeAiReply.isEmpty()
                ? (activeCallId.isEmpty() ? shortStatus(backendStatus.isEmpty() ? "AI oturumu hazırlanıyor..." : backendStatus) : "AI cevabi bekleniyor...")
                : activeAiReply;
        TextView line = text(aiText, 14, subText, false);
        line.setGravity(Gravity.CENTER);
        root.addView(line, fullWidth(dp(54)));

        Space spacer = new Space(this);
        root.addView(spacer, new LinearLayout.LayoutParams(1, 0, 1));
        addCallControls(video);
    }

    private void addCallControls(boolean dark) {
        LinearLayout top = new LinearLayout(this);
        top.setGravity(Gravity.CENTER);
        top.addView(callControl(muted ? "Mik. Aç" : "Sessiz", dark, () -> {
            muted = !muted;
            renderInCall();
        }));
        top.addView(callControl(speaker ? "Ahize" : "Hoparlör", dark, () -> {
            speaker = !speaker;
            renderInCall();
        }));
        top.addView(callControl(video ? "Video Kapat" : "Video", dark, () -> {
            video = !video;
            renderInCall();
        }));
        root.addView(top, fullWidth(dp(58)));

        LinearLayout bottom = new LinearLayout(this);
        bottom.setGravity(Gravity.CENTER);
        bottom.setPadding(0, dp(10), 0, 0);
        bottom.addView(callControl("AI Yanıt", dark, () -> requestAiReply("Devam et, seni dinliyorum.")));

        TextView end = text("Kapat", 17, Color.WHITE, true);
        end.setGravity(Gravity.CENTER);
        end.setBackground(round(Color.rgb(220, 70, 70), dp(54)));
        end.setOnClickListener(v -> endCall());
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(dp(116), dp(54));
        params.setMargins(dp(8), 0, dp(8), 0);
        bottom.addView(end, params);
        root.addView(bottom, fullWidth(dp(70)));
    }

    private void requestAiReply(String text) {
        if (activeCallId.isEmpty()) {
            activeAiReply = "AI oturumu hazırlanıyor...";
            renderInCall();
            return;
        }

        activeAiReply = "AI yazıyor...";
        renderInCall();
        backendClient.sendMessage(activeCallId, text, new BackendClient.MessageCallback() {
            @Override
            public void onResult(String reply, String provider, String audioUrl) {
                handler.post(() -> {
                    activeAiReply = reply;
                    playTtsAudio(audioUrl);
                    if (screen == Screen.IN_CALL) {
                        renderInCall();
                    }
                });
            }

            @Override
            public void onError(String message) {
                handler.post(() -> {
                    activeAiReply = shortStatus(message);
                    if (screen == Screen.IN_CALL) {
                        renderInCall();
                    }
                });
            }
        });
    }

    private void requestInitialGreeting() {
        if (initialGreetingRequested) {
            return;
        }
        if (activeCallId.isEmpty()) {
            pendingInitialGreeting = true;
            activeAiReply = "AI oturumu hazırlanıyor...";
            renderInCall();
            return;
        }
        pendingInitialGreeting = false;
        initialGreetingRequested = true;
        requestAiReply("Arama yeni acildi. Telefonda ilk sozu sen soyluyorsun. 'Alo, merhaba' diye basla, kendini kisaca tanit ve kullaniciyi dinledigini soyle.");
    }

    private String shortStatus(String value) {
        if (value == null || value.isEmpty()) {
            return "";
        }
        return value.length() <= 92 ? value : value.substring(0, 89) + "...";
    }

    private View callControl(String label, boolean dark, Runnable action) {
        TextView view = text(label, 14, dark ? Color.WHITE : TEXT, false);
        view.setGravity(Gravity.CENTER);
        view.setBackground(round(dark ? Color.rgb(58, 64, 72) : PANEL, dp(54)));
        view.setOnClickListener(v -> action.run());
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, dp(54), 1);
        params.setMargins(dp(5), 0, dp(5), 0);
        view.setLayoutParams(params);
        return view;
    }

    private void endCall() {
        stopCallAudio();
        handler.removeCallbacks(autoAnswer);
        handler.removeCallbacks(callTimer);
        if (activeContact != null) {
            recentCalls.add(0, new RecentCall(activeContact.name, "Bugün", formatClock(), true));
        }
        dialedNumber = "";
        showRecents();
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

    private Contact contactForLabel(String label) {
        String clean = label.replace(" (2)", "");
        for (Contact contact : contacts) {
            if (contact.name.equals(clean) || contact.phone.equals(clean)) {
                return contact;
            }
        }
        return new Contact("unknown", clean, clean, "Geçici AI arama simülasyonu", "Default", Color.rgb(134, 160, 225));
    }

    private void startRingAudio() {
        stopCallAudio();
        toneGenerator = new ToneGenerator(AudioManager.STREAM_MUSIC, 100);
        handler.post(ringLoop);
    }

    private void stopCallAudio() {
        handler.removeCallbacks(ringLoop);
        if (toneGenerator != null) {
            toneGenerator.release();
            toneGenerator = null;
        }
    }

    private void playKeyTone(String digit) {
        try {
            if (keyToneGenerator == null) {
                keyToneGenerator = new ToneGenerator(AudioManager.STREAM_MUSIC, 100);
            }
            keyToneGenerator.startTone(toneForDigit(digit), 120);
        } catch (Exception ignored) {
            stopKeyAudio();
        }
    }

    private int toneForDigit(String digit) {
        switch (digit) {
            case "1":
                return ToneGenerator.TONE_DTMF_1;
            case "2":
                return ToneGenerator.TONE_DTMF_2;
            case "3":
                return ToneGenerator.TONE_DTMF_3;
            case "4":
                return ToneGenerator.TONE_DTMF_4;
            case "5":
                return ToneGenerator.TONE_DTMF_5;
            case "6":
                return ToneGenerator.TONE_DTMF_6;
            case "7":
                return ToneGenerator.TONE_DTMF_7;
            case "8":
                return ToneGenerator.TONE_DTMF_8;
            case "9":
                return ToneGenerator.TONE_DTMF_9;
            case "0":
                return ToneGenerator.TONE_DTMF_0;
            case "*":
                return ToneGenerator.TONE_DTMF_S;
            case "#":
                return ToneGenerator.TONE_DTMF_P;
            default:
                return ToneGenerator.TONE_PROP_BEEP;
        }
    }

    private void stopKeyAudio() {
        if (keyToneGenerator != null) {
            try {
                keyToneGenerator.release();
            } catch (Exception ignored) {
            }
            keyToneGenerator = null;
        }
    }

    private void playTtsAudio(String audioUrl) {
        if (audioUrl == null || audioUrl.isEmpty()) {
            return;
        }
        stopTtsAudio();
        try {
            mediaPlayer = new MediaPlayer();
            mediaPlayer.setAudioStreamType(AudioManager.STREAM_MUSIC);
            mediaPlayer.setDataSource(audioUrl);
            mediaPlayer.setVolume(1.0f, 1.0f);
            mediaPlayer.setOnPreparedListener(MediaPlayer::start);
            mediaPlayer.setOnCompletionListener(player -> stopTtsAudio());
            mediaPlayer.setOnErrorListener((player, what, extra) -> {
                stopTtsAudio();
                return true;
            });
            mediaPlayer.prepareAsync();
        } catch (Exception ignored) {
            stopTtsAudio();
        }
    }

    private void stopTtsAudio() {
        if (mediaPlayer != null) {
            try {
                mediaPlayer.release();
            } catch (Exception ignored) {
            }
            mediaPlayer = null;
        }
    }

    private TextView text(String value, int sp, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(sp);
        view.setTextColor(color);
        view.setIncludeFontPadding(true);
        if (bold) {
            view.setTypeface(Typeface.DEFAULT_BOLD);
        }
        return view;
    }

    private TextView iconButton(String value, int sp, View.OnClickListener listener) {
        TextView view = text(value, sp, Color.BLACK, false);
        view.setGravity(Gravity.CENTER);
        view.setOnClickListener(listener);
        return view;
    }

    private TextView avatar(String value, int color) {
        TextView avatar = text(value, 20, Color.WHITE, true);
        avatar.setGravity(Gravity.CENTER);
        avatar.setBackground(round(color, dp(1000)));
        return avatar;
    }

    private void setPhoneIcon(TextView view, int sizeDp) {
        Drawable phone = getResources().getDrawable(R.drawable.ic_phone_white);
        int size = dp(sizeDp);
        phone.setBounds(0, 0, size, size);
        view.setCompoundDrawables(null, phone, null, null);
    }

    private GradientDrawable round(int color, int radius) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(radius);
        return drawable;
    }

    private LinearLayout.LayoutParams fullWidth(int height) {
        return new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, height);
    }

    private LinearLayout.LayoutParams square(int size) {
        return new LinearLayout.LayoutParams(size, size);
    }

    private boolean isCompactDialer() {
        float density = getResources().getDisplayMetrics().density;
        int heightDp = (int) (getResources().getDisplayMetrics().heightPixels / density);
        return heightDp < 560;
    }

    private int dialerKeyHeight() {
        return isCompactDialer() ? 48 : 68;
    }

    private String formatTime(int totalSeconds) {
        int minutes = totalSeconds / 60;
        int seconds = totalSeconds % 60;
        return String.format(Locale.US, "%02d:%02d", minutes, seconds);
    }

    private String formatClock() {
        java.text.SimpleDateFormat formatter = new java.text.SimpleDateFormat("HH:mm", Locale.US);
        return formatter.format(new java.util.Date());
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private static final class RecentCall {
        final String label;
        final String group;
        final String time;
        final boolean outgoing;

        RecentCall(String label, String group, String time, boolean outgoing) {
            this.label = label;
            this.group = group;
            this.time = time;
            this.outgoing = outgoing;
        }
    }
}
