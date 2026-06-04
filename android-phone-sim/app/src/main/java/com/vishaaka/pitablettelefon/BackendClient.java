package com.vishaaka.pitablettelefon;

import android.graphics.Color;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.OutputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

final class BackendClient {
    interface ContactsCallback {
        void onResult(List<Contact> contacts, String baseUrl);

        void onError(String message);
    }

    interface CallCallback {
        void onResult(String callId, String baseUrl);

        void onError(String message);
    }

    interface MessageCallback {
        void onResult(String reply, String provider);

        void onError(String message);
    }

    private static final String[] BASE_URLS = {
            "http://192.168.240.1:8080",
            "http://192.168.240.112:8080",
            "http://127.0.0.1:8080",
            "http://10.0.2.2:8080"
    };

    private volatile String workingBaseUrl;

    void fetchContacts(ContactsCallback callback) {
        new Thread(() -> {
            Exception lastError = null;
            for (String baseUrl : candidateUrls()) {
                try {
                    String body = get(baseUrl + "/contacts");
                    JSONArray array = new JSONArray(body);
                    List<Contact> contacts = new ArrayList<>();
                    for (int i = 0; i < array.length(); i++) {
                        JSONObject item = array.getJSONObject(i);
                        contacts.add(new Contact(
                                item.optString("id", "remote-" + i),
                                item.optString("name", "AI Kisi"),
                                item.optString("phone", ""),
                                item.optString("persona", "AI persona"),
                                item.optString("voice", "default"),
                                colorFor(i)
                        ));
                    }
                    workingBaseUrl = baseUrl;
                    callback.onResult(contacts, baseUrl);
                    return;
                } catch (Exception error) {
                    lastError = error;
                }
            }
            callback.onError(lastError == null ? "Backend bulunamadi" : lastError.getMessage());
        }).start();
    }

    void startCall(Contact contact, String mode, CallCallback callback) {
        new Thread(() -> {
            Exception lastError = null;
            for (String baseUrl : candidateUrls()) {
                try {
                    JSONObject request = new JSONObject();
                    request.put("contact_id", contact.id);
                    request.put("phone", contact.phone);
                    request.put("mode", mode);

                    String body = post(baseUrl + "/calls/start", request.toString());
                    JSONObject response = new JSONObject(body);
                    workingBaseUrl = baseUrl;
                    callback.onResult(response.optString("call_id", ""), baseUrl);
                    return;
                } catch (Exception error) {
                    lastError = error;
                }
            }
            callback.onError(lastError == null ? "Arama backend'e gonderilemedi" : lastError.getMessage());
        }).start();
    }

    void sendMessage(String callId, String text, MessageCallback callback) {
        new Thread(() -> {
            if (callId == null || callId.isEmpty()) {
                callback.onError("Aktif AI oturumu yok");
                return;
            }

            Exception lastError = null;
            for (String baseUrl : candidateUrls()) {
                try {
                    JSONObject request = new JSONObject();
                    request.put("text", text);

                    String body = post(baseUrl + "/calls/" + callId + "/message", request.toString());
                    JSONObject response = new JSONObject(body);
                    workingBaseUrl = baseUrl;
                    callback.onResult(response.optString("reply", ""), response.optString("provider", ""));
                    return;
                } catch (Exception error) {
                    lastError = error;
                }
            }
            callback.onError(lastError == null ? "AI mesaji gonderilemedi" : lastError.getMessage());
        }).start();
    }

    private List<String> candidateUrls() {
        List<String> urls = new ArrayList<>();
        if (workingBaseUrl != null && !workingBaseUrl.isEmpty()) {
            urls.add(workingBaseUrl);
        }
        for (String baseUrl : BASE_URLS) {
            if (!urls.contains(baseUrl)) {
                urls.add(baseUrl);
            }
        }
        return urls;
    }

    private String get(String url) throws Exception {
        HttpURLConnection connection = open(url, "GET");
        return read(connection);
    }

    private String post(String url, String json) throws Exception {
        HttpURLConnection connection = open(url, "POST");
        connection.setDoOutput(true);
        byte[] payload = json.getBytes(StandardCharsets.UTF_8);
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setRequestProperty("Content-Length", String.valueOf(payload.length));
        try (OutputStream output = connection.getOutputStream()) {
            output.write(payload);
        }
        return read(connection);
    }

    private HttpURLConnection open(String url, String method) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
        connection.setRequestMethod(method);
        connection.setConnectTimeout(800);
        connection.setReadTimeout(1200);
        return connection;
    }

    private String read(HttpURLConnection connection) throws Exception {
        int code = connection.getResponseCode();
        if (code < 200 || code >= 300) {
            throw new IllegalStateException("HTTP " + code);
        }
        StringBuilder builder = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                builder.append(line);
            }
        }
        return builder.toString();
    }

    private int colorFor(int index) {
        int[] colors = {
                Color.rgb(61, 126, 255),
                Color.rgb(24, 160, 88),
                Color.rgb(230, 180, 80),
                Color.rgb(214, 69, 69),
                Color.rgb(132, 94, 247),
                Color.rgb(0, 150, 136)
        };
        return colors[index % colors.length];
    }
}
