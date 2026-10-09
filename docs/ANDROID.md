# Honor Agent Android App

This directory contains a native Android client for the HonorAgent API.

The APK does not embed the Python/FastAPI server. Run the HonorAgent API separately, then point the app at that API base URL.

## Features

- Check `/health`
- Analyze a GitHub repository through `/api/v1/github/analyze`
- Create and run a demo task through `/api/v1/tasks`
- Supports Android emulator and physical devices

## Build APK Locally

Requirements:

- JDK 17
- Android SDK
- Gradle

Commands:

```bash
cd android
gradle :app:assembleDebug
```

APK output:

```txt
android/app/build/outputs/apk/debug/app-debug.apk
```

## Build APK With GitHub Actions

1. Push the repository to GitHub.
2. Open the repository on GitHub.
3. Go to `Actions`.
4. Select `Android APK`.
5. Click `Run workflow`.
6. When the workflow finishes, open the run page.
7. Download the `honor-agent-debug-apk` artifact.

## Start the HonorAgent API

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
honor-agent
```

Verify:

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status":"ok","service":"honor-agent"}
```

## Install the APK

### Android Emulator

```bash
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

Use this API URL in the app:

```txt
http://10.0.2.2:8000
```

`10.0.2.2` is the emulator alias for the host machine.

### Physical Android Phone

1. Connect the phone and computer to the same Wi-Fi network.
2. Start the API server on the computer.
3. Find the computer LAN IP:

```bash
ipconfig getifaddr en0
```

4. Use this API URL in the app:

```txt
http://<computer-lan-ip>:8000
```

Example:

```txt
http://192.168.1.23:8000
```

5. Install the APK with Android Studio or:

```bash
adb install -r app-debug.apk
```

## How To Use

1. Open `Honor Agent` on Android.
2. Set `API Base URL`.
   - Emulator: `http://10.0.2.2:8000`
   - Physical phone: `http://<computer-lan-ip>:8000`
3. Keep `API Key` as `dev-api-key` for the current MVP server.
4. Tap `Check API Health`.
5. Tap `Analyze GitHub Repository`.
6. Tap `Create and Run Demo Task`.

## Troubleshooting

### `Error: failed to connect`

- Confirm the API server is running.
- For emulator, use `10.0.2.2`, not `localhost`.
- For physical phone, use the computer LAN IP, not `127.0.0.1`.
- Confirm firewall settings allow inbound connections to port `8000`.

### GitHub analysis fails

- Public repositories work without credentials.
- For private repositories, set `GITHUB_TOKEN` before starting the API server.

```bash
export GITHUB_TOKEN=github_pat_xxx
honor-agent
```

### Release APK

The current workflow builds a debug APK for testing. For production distribution, create a signing key and add a release build variant.

