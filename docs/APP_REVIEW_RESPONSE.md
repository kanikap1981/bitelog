# BiteLog App Review response

Prepared for BiteLog 1.6.4 (build 24) in response to Guideline 2.1, Information Needed.

## Resolution Center reply

Hello App Review,

Thank you for reviewing BiteLog. Please find the requested information below.

### Purpose and value

BiteLog helps an athlete follow a nutrition plan supplied by their own dietitian and prepare a clear weekly update for that dietitian. The app addresses the difficulty of reconstructing meals, movement, and relevant context from memory at the end of a week.

The athlete can upload the plan they already received, log meals manually, by photograph, or by voice, review estimated calories, carbohydrates, and protein before saving, add journal reflections, optionally read movement data from Apple Health, and create a seven-day summary. BiteLog opens the athlete's configured email application with the summary addressed to their dietitian. The athlete reviews and sends the message themselves.

The intended audience is adults and athletes who already work with a qualified dietitian. BiteLog supports record keeping and communication. It does not diagnose, treat, prescribe, or replace professional medical or nutrition advice. Meal nutrition produced from a photograph or voice description is clearly an estimate and is reviewed by the athlete before it is saved. When a plan does not contain explicit numeric targets, the app labels calculated allowances as estimates rather than representing them as dietitian-authored targets.

The initial release is a controlled launch for approximately 20 to 30 athletes from a dietitian's client base. This small first cohort will let us validate the logging and weekly communication workflow with real users and incorporate feedback before expanding availability. The product is not limited to one dietitian or practice: each athlete configures their own dietitian and can use the plan that dietitian already provides.

### Access and review instructions

No account, login, subscription, or special hardware is required for the main workflow.

1. Launch BiteLog and complete the profile with an athlete name, dietitian name, and a valid email address. Reviewers may use their own email address.
2. Open **Plan**, choose a PDF or image of a nutrition plan, and tap **Analyze and save plan**. A sample plan can be attached to this App Review message. Reviewers may also use any simple nutrition-plan PDF or image.
3. Open **Today**, tap the add button, and choose one of the following:
   - photograph or select a meal image, then tap **Estimate from photo**;
   - record a spoken meal description; or
   - enter a meal manually.
4. Review the meal name, calories, carbohydrates, protein, confidence, and assumptions, then save it. The saved meal appears under **Meals today** and in **Food Log**, where it can also be deleted.
5. Optional: on **Today**, tap **Sync movement** and allow Apple Health read access. If permission is declined, the rest of BiteLog remains usable.
6. Open **Journal** to add a written or spoken reflection.
7. Open **Progress** and tap **Build my weekly update for the dietitian**. The update combines meal logs, plan adherence, journal reflections, and available seven-day movement totals.
8. Tap **Email dietitian**. BiteLog opens the configured iOS email application with a draft. The user reviews and sends it; BiteLog never sends email automatically.

Camera, photo-library, microphone, Apple Health, and Mail behaviour requires the corresponding system permission or configured application. A reviewer can complete the principal workflow using an existing meal photo, manual meal entry, and a plan PDF without granting optional Apple Health access.

### External services

- **BiteLog production API**, hosted on Vercel at `https://bitelog-api.vercel.app`, receives plan documents, meal images, spoken-meal audio, and journal audio only when the user explicitly requests analysis or transcription.
- **OpenAI Responses API** is called by the BiteLog server for structured meal estimation, nutrition-plan extraction, and transcription. The OpenAI credential is held only in protected server configuration and is not included in the iOS app.
- **Apple HealthKit** is an optional, permission-based, read-only source for steps, active calories, and workout minutes. BiteLog does not write Health data. Health data remains on the device and is included in the weekly draft only after the user syncs it.
- **The user's configured iOS email application** handles the final weekly email draft through the standard mail link. BiteLog does not operate an email delivery service and does not send messages without the user.

The athlete's profile, extracted plan, meal log, journal, and cached Health summary are stored locally within the app on the device. BiteLog currently has no user account or cloud-sync service.

### Regional availability

BiteLog has no region-gated features and is designed to operate consistently in every territory selected for distribution in App Store Connect. Its production API is accessed over HTTPS. Functions that depend on Apple Health or the user's email application require those Apple services to be available and configured on the device.

### Regulatory and content clarification

BiteLog is a logging and communication tool. It is not a medical device and does not provide diagnosis, treatment, or a substitute for a dietitian or other qualified professional. The app does not ship with protected third-party dietitian plans. Users choose and provide plans they are entitled to use. AI-generated nutrition values are identified as estimates and require user review before saving.

We have attached a physical-iPhone screen recording beginning with app launch and demonstrating the normal workflow. We have also attached a sample plan for review.

Thank you.

## App Review Notes field

BiteLog helps an athlete follow a nutrition plan supplied by their own dietitian and prepare a weekly update. No account or login is required.

The initial launch will serve approximately 20 to 30 athletes from a dietitian's client base while we validate the workflow before broader availability. BiteLog is designed to work with any dietitian and is not restricted to a single practice.

Review path: launch the app and complete the profile; open Plan and analyze the attached sample PDF or any nutrition-plan image/PDF; open Today and add a meal manually, by photo, or by voice; review the estimated calories, carbohydrates, protein, confidence, and assumptions before saving; optionally sync movement from Apple Health; add a Journal reflection; then open Progress, build the weekly update, and tap Email dietitian to open an iOS email draft.

Apple Health is optional and read-only. The app remains usable if Health access is declined. BiteLog does not send email automatically. Records are stored locally on the device. The production analysis API is `https://bitelog-api.vercel.app`, hosted on Vercel, and calls OpenAI server-side; no provider API key exists in the app.

BiteLog supports record keeping and communication with an existing dietitian. It does not diagnose, treat, prescribe, or replace professional advice. Photo and voice nutrition results are estimates that the athlete reviews before saving.

## Physical-iPhone recording script

Use a physical iPhone running the latest available iOS. Enable screen recording and begin on the Home Screen so the recording shows BiteLog being launched.

1. Tap the BiteLog icon and briefly show Today.
2. Open Profile/Settings and show that the athlete and dietitian details are configured. Do not expose a private email address in the recording; use a review address if needed.
3. Open Plan, select the sample plan, tap Analyze and save plan, and show the extracted plan summary and weekly allowance.
4. Open Today, add a meal from a photograph, tap Estimate from photo, and wait for the result.
5. Show the returned meal name, calories, carbohydrates, protein, confidence, and assumptions. Tap Save.
6. Show the meal under Meals today, then open Food Log and show the same saved meal and its Delete control. Do not delete it yet.
7. Return to Today, tap Sync movement, and show the movement section. If the recording device has no useful Health data, this step may be omitted and Apple Health can be described as optional in the written reply.
8. Open Journal and add a short reflection such as, “Training felt strong this week and hunger was manageable.” Show it in This week's notes.
9. Open Progress and tap Build my weekly update for the dietitian.
10. Scroll through the nutrition, plan, movement, and Journal sections in the generated update.
11. Tap Email dietitian and show the populated email draft. Do not send it. Return to BiteLog.
12. End the recording after returning to the Progress screen.

Keep the recording continuous, with no editing that obscures the workflow. Avoid notifications and personal data. The photo and plan analysis steps require an internet connection and may take several seconds.

## Submission checklist

- Attach the screen recording to the Resolution Center reply.
- Attach a sample nutrition-plan PDF or image.
- Paste the Resolution Center reply above into Apple's message field.
- Paste the shorter text into App Review Notes for the submitted version.
- Confirm the reviewed build is 1.6.4 (24).
- Confirm the support URL and privacy-policy URL are reachable without authentication.
- Keep the review profile email and sample plan free of unnecessary personal information.
