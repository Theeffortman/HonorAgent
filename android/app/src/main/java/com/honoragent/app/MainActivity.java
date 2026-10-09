package com.honoragent.app;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    private EditText baseUrlInput;
    private EditText apiKeyInput;
    private EditText githubUrlInput;
    private TextView outputView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        baseUrlInput = findViewById(R.id.baseUrlInput);
        apiKeyInput = findViewById(R.id.apiKeyInput);
        githubUrlInput = findViewById(R.id.githubUrlInput);
        outputView = findViewById(R.id.outputView);

        Button healthButton = findViewById(R.id.healthButton);
        Button githubButton = findViewById(R.id.githubButton);
        Button taskButton = findViewById(R.id.taskButton);

        healthButton.setOnClickListener(v -> runAsync("Checking API health...", this::checkHealth));
        githubButton.setOnClickListener(v -> runAsync("Analyzing GitHub repository...", this::analyzeGithub));
        taskButton.setOnClickListener(v -> runAsync("Creating demo task...", this::createAndRunTask));
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        executor.shutdownNow();
    }

    private void runAsync(String status, Action action) {
        setButtonsEnabled(false);
        outputView.setText(status);
        executor.submit(() -> {
            try {
                String result = action.run();
                runOnUiThread(() -> outputView.setText(result));
            } catch (Exception error) {
                runOnUiThread(() -> outputView.setText("Error: " + error.getMessage()));
            } finally {
                runOnUiThread(() -> setButtonsEnabled(true));
            }
        });
    }

    private void setButtonsEnabled(boolean enabled) {
        int[] ids = {R.id.healthButton, R.id.githubButton, R.id.taskButton};
        for (int id : ids) {
            View view = findViewById(id);
            view.setEnabled(enabled);
        }
    }

    private String checkHealth() throws Exception {
        return request("GET", "/health", null).toString(2);
    }

    private String analyzeGithub() throws Exception {
        JSONObject body = new JSONObject()
                .put("url", githubUrlInput.getText().toString().trim())
                .put("include_remote", true);
        return request("POST", "/api/v1/github/analyze", body).toString(2);
    }

    private String createAndRunTask() throws Exception {
        JSONObject taskBody = new JSONObject()
                .put("name", "Android demo task")
                .put("description", "Created from the Honor Agent Android app")
                .put("agents", new org.json.JSONArray().put("data_analyst"))
                .put("priority", "normal")
                .put("params", new JSONObject().put("data_source", "android_app"));

        JSONObject createResponse = request("POST", "/api/v1/tasks", taskBody);
        String taskId = createResponse.getJSONObject("data").getString("id");
        JSONObject runResponse = request("POST", "/api/v1/tasks/" + taskId + "/run", null);

        return "Created task: " + taskId + "\n\n" + runResponse.toString(2);
    }

    private JSONObject request(String method, String path, JSONObject body) throws Exception {
        String baseUrl = baseUrlInput.getText().toString().trim();
        if (baseUrl.endsWith("/")) {
            baseUrl = baseUrl.substring(0, baseUrl.length() - 1);
        }

        URL url = new URL(baseUrl + path);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod(method);
        connection.setConnectTimeout(15000);
        connection.setReadTimeout(30000);
        connection.setRequestProperty("Accept", "application/json");
        connection.setRequestProperty("Authorization", "Bearer " + apiKeyInput.getText().toString().trim());

        if (body != null) {
            byte[] bytes = body.toString().getBytes(StandardCharsets.UTF_8);
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "application/json");
            connection.setRequestProperty("Content-Length", String.valueOf(bytes.length));
            try (OutputStream output = connection.getOutputStream()) {
                output.write(bytes);
            }
        }

        int code = connection.getResponseCode();
        InputStream stream = code >= 200 && code < 300
                ? connection.getInputStream()
                : connection.getErrorStream();
        String response = readAll(stream);
        if (code < 200 || code >= 300) {
            throw new IllegalStateException("HTTP " + code + ": " + response);
        }
        return new JSONObject(response);
    }

    private static String readAll(InputStream stream) throws Exception {
        if (stream == null) {
            return "";
        }
        StringBuilder builder = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                builder.append(line);
            }
        }
        return builder.toString();
    }

    private interface Action {
        String run() throws Exception;
    }
}

