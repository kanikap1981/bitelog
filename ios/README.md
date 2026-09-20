# BiteLog iOS v1.2

Open `BiteLogHealth.xcodeproj` in Xcode.

1. Select the BiteLog target.
2. Signing & Capabilities -> Automatically manage signing -> ON.
3. Pick your Apple Development Team.
4. Keep HealthKit enabled.
5. Select your iPhone and Run.
6. In BiteLog Settings, enter the BiteLog backend URL.

For local testing, run the backend on your Mac with `--host 0.0.0.0`, put the iPhone and Mac on the same Wi-Fi, and use the Mac's LAN IP such as `http://192.168.1.25:8000`.

The app never contains the OpenAI API key.
