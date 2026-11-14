# Current state / handoff

## November 14, 2026 — staged invite-only access implemented

- The backend now redeems private invite codes at `POST /v1/invites/redeem` and issues signed access tokens that expire after five days.
- Photo analysis, spoken-meal analysis, journal transcription, plan analysis, object analysis, and upload presigning can require the signed token. Enforcement is deliberately **off** until an invite-enabled iPhone build has passed device testing and reached testers.
- The iPhone app now shows **Your BiteLog Diet Program** before profile onboarding, redeems the code server-side, stores only the signed token and expiry, and sends the token with AI and upload requests. No plaintext invite codes are bundled in the app.
- Vercel production has `INVITE_CODE_HASHES` and `INVITE_TOKEN_SECRET` stored as non-revealable secrets, plus a five-day TTL and `INVITE_ENFORCEMENT_ENABLED=false`. Commit `8a0f43a` deployed successfully and is live at `https://bitelog-api.vercel.app`.
- The ten reserved tester codes remain the private distribution list previously supplied to Kanika. Their plaintext values are not committed.
- Automated verification passes: 19 backend unit tests, the bundled iOS JavaScript behavior/syntax test, Python compilation, and diff validation.
- Live verification passed: `/health` returned OK, a reserved code returned a token for `tester-01` with a 432,000-second lifetime, and a no-token analysis request was not rejected by invite authorization. The app source is still BiteLog 1.6.4 build 24; a new build number, iPhone installation, TestFlight upload, and enforcement activation have not been performed.

## November 12, 2026 — grams-based photo portions saved locally

- Photo analysis now includes an estimated total photographed weight in grams in addition to meal name, calories, carbohydrates, protein, confidence, description, and assumptions.
- After a photo estimate, athletes may optionally enter the number of grams they expect to eat. BiteLog scales all three nutrition values from the estimated full-meal weight, while leaving the fields editable for confirmation.
- Saved meals retain the selected gram amount and show it in Today and Food Log.
- Photo-meal persistence is now transactional and verified before the sheet closes. A failed write is rolled back and produces a visible error instead of increasing in-memory totals without a durable meal.
- Only a 240px thumbnail is stored with a meal rather than the full analysis image. On quota pressure, BiteLog removes legacy oversized meal thumbnails while preserving the meal records, then retries.
- Automated verification passes: 15 backend unit tests, the bundled JavaScript behavior/syntax test, Python compilation, and diff validation.
- iPhone testing, production backend deployment, build-number increment, TestFlight/App Store upload, and the deferred visual redesign have not been performed for this change.

## November 1, 2026 — App Store resubmission waiting for review

- BiteLog 1.6.4 build 24 is submitted for public App Review under submission `bb77318b-a96e-461e-9a00-0479b149e3c3`; Apple reports `Waiting for Review`.
- The App Review Notes contain the requested purpose, audience, access path, external-service disclosure, regional consistency, and regulatory clarification.
- `BiteLog-App-Review-Edited-Final.mp4` is attached in App Store Connect. The recording was captured on the physical iPhone, begins with launch from the Home Screen, and demonstrates the principal workflow with personal inbox and email addresses removed or redacted.
- TestFlight build 24 remains separately `Waiting for Review` and is assigned to the internal `Bitelog testing` group and external `Amie testing` group. Amie cannot install build 24 until Apple approves the external beta.
- Automatic App Store release is selected after approval.

## November 1, 2026 — build 24 reinstalled on Kanika's iPhone

- Rebuilt the clean committed 1.6.4 source as build 24 with the Modern Health development signing profile and HealthKit entitlement.
- Verified the installable app reports bundle identifier `au.com.themodernhealth.BiteLog`, version `1.6.4`, and build `24`.
- Installed the app successfully on Kanika's connected iPhone 17 Pro and launched it through `devicectl`.
- The native launch succeeded. Final feature interaction remains a manual on-phone check.

## November 1, 2026 — build 24 submitted for external TestFlight review

- BiteLog 1.6.4 build 24 finished App Store Connect processing and was added to the existing external TestFlight group `Amie testing`.
- Test instructions ask testers to cover photo and voice meal logging, calories/carbohydrates/protein/confidence/assumptions, PDF/image plan upload, save/delete, Apple Health, Journal, weekly update, and the email draft.
- Apple now reports build 24 as `Waiting for Review`; it is not yet installable by external testers. Build 23 remains in `Testing` with eight recorded sessions.
- The external group reports zero named testers and uses the public link `https://testflight.apple.com/join/Pu6yxcTU`. Amie can continue using build 23 through that link while build 24 awaits Beta App Review.
- The `finish-bitelog-build-24-testflight` monitor now watches for approval, rejection, information requests, or another actionable error and will verify the public link when approval occurs.

## November 1, 2026 — App Review information package prepared

- Apple previously requested additional information under Guideline 2.1 for build 23: a physical-iPhone workflow recording, product and audience explanation, reviewer access instructions, external-service disclosure, regional-availability confirmation, and regulatory/content clarification.
- `docs/APP_REVIEW_RESPONSE.md` now contains a complete Resolution Center reply, concise App Review Notes, a physical-iPhone recording script, and a submission checklist for BiteLog 1.6.4 build 24.
- A fictional, non-personal sample plan was created at `output/pdf/BiteLog-App-Review-Sample-Plan.pdf` and visually verified for use as the App Review attachment.
- The sample PDF was analyzed through the live production endpoint with HTTP 200 and returned its explicit 2,200 kcal/day, 140g protein/day, 15,400 kcal/week, and 980g protein/week targets without marking them as estimates.
- The response accurately describes BiteLog as a local-first logging and dietitian-communication tool, identifies optional read-only Apple Health access, discloses the Vercel-hosted production API and server-side OpenAI use, and states that estimates require athlete review.
- The supplied 32-second recording was reviewed and should be replaced: it starts inside the app, does not show a new photo estimate being calculated and saved, exposes personal inbox/email information, and shows an unsuccessful Apple Health refresh.
- Apple still requires a replacement screen recording and the attachments to be supplied in App Store Connect. Their submission cannot be inferred from the code upload alone.

## November 1, 2026 — carbohydrates added to meal estimates

- Photo and spoken-meal analysis now return calories, carbohydrates, protein, confidence, and assumptions from the server.
- The iOS meal confirmation form shows all three nutrition values. Carbohydrates are saved with manual, photo, and voice meals and appear in Meals today and Food Log.
- The production backend at `https://bitelog-api.vercel.app` is deployed with the new contract. A live oatmeal-photo request returned HTTP 200 with 440 kcal, 78g carbohydrates, and 17g protein; a live spoken-meal request returned HTTP 200 with 410 kcal, 56g carbohydrates, and 22g protein.
- All 15 backend tests, the bundled iOS JavaScript behavior/syntax test, and Info.plist validation pass.
- BiteLog remains version 1.6.4 build 24. The archive was inspected before distribution and reports version 1.6.4, build 24. Its signed App Store upload succeeded with the Modern Health team. Apple is processing the uploaded build before it can be assigned to Amie’s TestFlight group.

## November 1, 2026 — meal photo and plan analysis restored (1.6.4 build 24 source)

- Production photo and plan analysis had a shared operational failure: OpenAI returned `401 invalid_api_key` before either analyzer could process its input. The protected Vercel credential was rotated and production was redeployed at `https://bitelog-api.vercel.app`.
- Meal photos now retain up to 1280px at JPEG quality 0.84. The backend requests high-detail vision and explicitly estimates every visible component, portions, cooking fats, sauces, and toppings before returning the meal name, calories, protein, confidence, description, and assumptions.
- The server model default was updated from the stale `gpt-5.6-luna` configuration to `gpt-6.1-sol`.
- Plan PDFs continue to use the Responses API file input and plan images use high-detail vision. Provider credential and quota failures now produce accurate, actionable messages without exposing provider data.
- Live production checks returned HTTP 200 for health, two supplied food photos, the full five-page `Kanika Pandey V8.pdf`, a rendered image of its first page, a spoken meal, and journal transcription. The PDF preserved the complete schedule and produced estimated allowances because the plan contains no explicit calorie or protein target.
- All 15 backend tests, the bundled iOS JavaScript behavior/syntax test, plist/entitlement lint, diff validation, and the post-deployment error scan pass.
- The source is version 1.6.4 build 24. Full Xcode 26.3 is installed; build 24 has not yet been archived or uploaded to App Store Connect.
- Apple Health permissions/data, the native Mail composer, camera capture, save/delete presentation, and the visual quality of real iPhone photos still require a manual physical-device pass before submission.

## What has been proven
- Physical iPhone detected by Xcode.
- Developer Mode enabled.
- App signing configured with an Xcode-managed profile.
- Developer certificate trusted on iPhone.
- App installs and launches.
- Backend virtualenv and requirements install successfully.
- Uvicorn reaches `Application startup complete` on local Mac.

## Bugs already encountered and fixed
1. `No profiles for 'com.bitelog.app' were found`
   - Fixed by automatic signing, selecting a development team, and using a unique bundle identifier.
2. iPhone not available for development
   - Fixed by enabling Developer Mode on device.
3. `missing or invalid CFBundleExecutable`
   - Fixed by adding `CFBundleExecutable = $(EXECUTABLE_NAME)` to Info.plist.
4. Developer App Certificate not trusted
   - Fixed in iPhone Settings -> General -> VPN & Device Management.
5. Backend crash on Python 3.9: `unsupported operand type(s) for |: 'type' and 'NoneType'`
   - Fixed by using `typing.Optional` in `backend/app/config.py`.

## Still unresolved / unverified
- Apple Health appears in capabilities but sync is not confirmed working.
- Photo estimation has passed automated route/UI-handler tests, a live provider contract smoke test, and physical-iPhone API requests. The updated source build built, installed, and launched on Kanika's iPhone; the device reached `/health` and received HTTP 200 from two photo-analysis requests. Final Save-sheet interaction and nutrition accuracy remain unverified.
- Existing `gpt-5.6-luna` model and Responses API schema were checked against current official documentation and passed the live contract smoke test.
- Current local networking uses HTTP for development only.

## Current local test flow
1. `cd backend`
2. Activate `.venv`.
3. Run Uvicorn on `0.0.0.0:8000`.
4. Find Mac LAN IP with `ipconfig getifaddr en0`.
5. In current source build, configure BiteLog API base URL to `http://<LAN-IP>:8000`.
6. Test `http://<LAN-IP>:8000/health` from iPhone Safari first.
7. Then test meal photo estimation.

## UX direction
Use Browserbase-inspired design principles:
- large editorial typography
- strong black/white hierarchy
- bright accent for primary action
- concise capability-led copy
- fewer controls visible at once
- modular sections/cards

Do not copy Browserbase text or brand identity.

## September 20, 2026 — photo analysis reliability

- The selected project is `/Users/kanika/Documents/Healthapp/BiteLog-v1.2-production`.
- Legacy full analysis URLs are normalized to a base URL; the app appends the route exactly once.
- Photo loading, analysis timeout, malformed output, provider refusal/failure, and connectivity failures show readable errors. Cancelled/stale requests cannot fill another meal.
- The estimate retains decimal protein values, displays confidence/assumptions, and requires athlete confirmation before save.
- Settings includes a `/health` connection check. Backend responses/logs have request IDs without logging photos or credentials.
- Seven backend unittest cases pass with the existing Python 3.9.6 environment; Node handler tests pass. No dependency versions changed.
- A live route call using a valid synthetic PNG returned HTTP 200 and all six structured fields. The backend was also reachable through the Mac's active LAN address, `http://10.0.0.214:8000/health`, and Xcode reported `Running BiteLog on Kanika's iPhone` for this checkout. A real meal photo and the in-app LAN request still need validation.
- No OpenAI key patterns were found in iOS source. The GitHub repository was empty when connected, so there was no prior Git history to audit.
- Full Xcode is installed at `/Users/kanika/Downloads/Xcode.app` even though the shell's active developer directory still points to Command Line Tools. The build was run through the Xcode UI against the physical device.

## Repository continuity

The selected folder is now the local Git checkout on branch `main`, with `origin` set to `https://github.com/kanikap1981/bitelog.git`. The remote was verified to be empty before initialization, so there were no remote changes to pull or conflicts to resolve. The initial local commit contains the current project and handoff. It has not been pushed because project-level push authorization has not yet been given.

## September 20, 2026 — save-sheet dismissal fix

- Device testing found that meal and Settings values persisted, but their modal sheets did not dismiss after Save. Daily calories increasing confirmed persistence and rendering were already working.
- Both flows had the same cause: direct reliance on `HTMLDialogElement.close()` inside WKWebView.
- All dialogs now use shared `openDialog` / `closeDialog` helpers. Closing still calls the native API, then explicitly removes the `open` state and forces immediate visual dismissal as a WebKit fallback.
- The UI regression test now proves meal persistence, Settings persistence, render-before-close ordering, and dismissal even when the simulated native `close()` is a no-op.
- The fixed bundle built, installed, and launched on Kanika's physical iPhone. Final on-device interaction confirmation is still pending.
- Backend logs then recorded three successful `/health` requests and two successful `POST /v1/meals/analyze-inline` requests from the physical iPhone at `10.0.0.217`, proving the in-app LAN and AI request path.

## September 20, 2026 — persistent dismissal and meal visibility fix

- Device feedback showed the first dialog fallback was still insufficient on the physical iPhone. The fallback now keeps `display: none !important` on a closed dialog until the next explicit open, preventing WKWebView from making the sheet visible again on a later frame.
- Save meal now explicitly selects the Today tab before rendering and closing. The saved meal therefore appears in the Today list immediately, as well as contributing to daily totals.
- Each logged meal has a clearer `Delete` action. Deleting still asks for confirmation, persists the removal, and refreshes daily totals and the list.
- Settings Save uses the same persistent close helper, so saving the API URL and targets closes the Settings sheet.
- The Settings sheet displays `BiteLog 1.2.1 · build 3`, making it possible to confirm that the corrected bundle is installed instead of an older cached build.
- The corrected build installed and launched on Kanika's physical iPhone; Xcode reported `Running BiteLog on Kanika’s iPhone`. Final tap-through confirmation of Save and Delete behavior remains a device test.
- Seven backend tests and the iOS JavaScript behavior test pass. The latter covers meal persistence, explicit Today selection, rendering, persistent WKWebView dismissal, reopening, Settings persistence, and Settings dismissal.



## October 17, 2026 — complete local MVP flow (1.5.0 build 9)

- BiteLog now separates Today, Food Log, Journal, Plan, and Progress. Today contains the current day's meals; Food Log shows the ongoing meal history and supports immediate deletion.
- Manual, photo, and spoken meal logs all save into the same daily store. Spoken meals are transcribed and receive server-side calorie/protein estimates. Unclear or failed recordings are discarded.
- Journal voice notes are transcribed as reflections only. They never affect nutrition totals and are included in the seven-day dietitian email draft.
- Athlete name, dietitian name, and dietitian email are configurable in Settings. Weekly progress and the email draft compare seven-day logged nutrition with the active plan allowance.
- A dietitian plan can be a PDF, supported image, text file, or notes. The original document is saved locally in IndexedDB and can be reopened from Plan. Structured extraction stores goal, meal windows/options, hydration, weekly rules, recipes, daily/weekly calorie and protein ranges, summary, and assumptions.
- The five-page sample `Kanika Pandey V8.pdf` was saved and analyzed end-to-end. It contains a fat-loss meal schedule, 2–3 L hydration, weekly food rules, and recipes, but no explicit calorie/protein totals. BiteLog therefore displays estimated ranges with a visible estimate label instead of presenting them as dietitian targets.
- The app and `/health` report version 1.5.0; the iPhone bundle is build 9.
- Validation passes: 14 backend unit tests, the bundled JavaScript behavior/syntax test, `git diff --check`, Info.plist lint, real sample-plan analysis through FastAPI, and a signed generic iOS device build with HealthKit entitlement.

### Remaining limits

- BiteLog 1.5.1 build 10 built, signed, and installed successfully on Kanika’s connected iPhone. Final visual and interaction confirmation remains a manual device check.
- Apple Health still needs a physical-device permission and data validation pass.
- Meals, profile, extracted plan data, and the original plan currently live only in the app's local WebView storage. There is no user account, cloud sync, or server database yet, so deleting the app removes local data.
- The local development backend uses HTTP, broad CORS, and no API authentication. Production deployment and hardening remain future work.


## October 17, 2026 — restrained palette and typography (1.5.1 build 10)

- The active interface now uses neutral system surfaces, charcoal text, gray metadata, and one dark green accent (`#207A55`). Red is reserved for destructive/error states.
- Blue, orange, purple, lime, and bright green no longer compete as active interface accents. Calories and protein use the same visual language because color does not encode different health judgments.
- The green accent passes WCAG normal-text contrast against white (5.28:1) and the light system background (4.73:1).
- Typography now uses the iOS system sans-serif with a calmer hierarchy inspired by Spotify's content-first rhythm: one strong page title, medium section headings, regular body copy, sentence-case labels, and reduced letter compression.
- Marketing-style headings were simplified to direct names such as “Today’s targets,” “Weekly progress,” “Your nutrition plan,” and “Add to BiteLog.”
- Visual browser checks covered Today, Progress, and the Add sheet. The JavaScript regression test, Info.plist validation, diff check, and iPhone 17 simulator build pass.


## October 17, 2026 — build 10 physical-device installation

- Xcode detected Kanika’s iPhone 17 Pro as connected.
- BiteLog 1.5.1 build 10 compiled and signed for the physical device with the existing HealthKit entitlement and provisioning profile.
- `devicectl` installed bundle `com.kanikapandey.BiteLog` successfully. The app was not launched remotely; confirm the new typography and palette manually on the phone.


## October 17, 2026 — faster photo estimation (1.5.2 build 11)

- Phone photos are reduced from a maximum 900px/0.76 JPEG to 640px/0.68 before upload.
- The server now requests `detail: low` instead of `detail: high`; the response contract and server-only API key are unchanged.
- Privacy-safe provider logs include model, detail, status, and duration without image data or credentials.
- A live route request returned all six structured fields in 3.10 seconds, with 3.05 seconds spent in the provider call.
- All 14 backend tests and the bundled UI behavior test pass. Build 11 built, signed, and installed successfully on Kanika’s iPhone.


## October 17, 2026 — home logo (1.5.3 build 12)

- The Today header now uses the selected BiteLog wordmark with a large capital `B`, smaller `log`, and the existing dark green accent dot.
- Build 12 compiled, signed, and installed successfully on the connected iPhone. Physical-device visual confirmation remains manual.


## October 17, 2026 — iPhone app icon (1.5.4 build 13)

- The iOS target now has an `AppIcon` asset catalog with a 1024×1024 opaque BiteLog icon and target build settings for Debug and Release.
- Xcode compiled the icon into `AppIcon60x60@2x.png` and `Assets.car`; build 13 was signed and installed successfully on the connected iPhone.
- The icon is dark green with a large ivory `B` and smaller `log`, matching the in-app identity.


## October 17, 2026 — onboarding and weekly workflow (1.5.6 build 15)

- First launch now collects the athlete name, dietitian name, and dietitian email before normal use. Profile editing remains available from settings.
- Development API configuration is no longer exposed to athletes; the current local endpoint is bundled as product configuration.
- The Plan upload screen has a simplified PDF/photo flow and separate saved-plan output.
- Progress has one weekly-update action. It reveals the summary directly, and native iOS handling opens the email draft.
- UI regression checks, all 14 backend tests, plist validation, signed device build, and physical-device installation pass.


## October 17, 2026 — detailed green progress design (1.5.7 build 16)

- Journal, Plan, and weekly-update actions now share the green outlined visual treatment introduced by the Plan chooser.
- Weekly Progress uses a composed seven-day overview, green section accents, refined averages with units, a meal-count pill, and green consistency indicators.
- Build 16 passed the JavaScript behavior/syntax test, plist validation, diff validation, signed device build, and physical-device installation.


## October 17, 2026 — compact Today screen (1.5.8 build 17)

- Today now has one compact header row with the BiteLog identity, centered day/date, and settings.
- Daily calories, protein, remaining calories, and progress bars now live in one restrained nutrition card with smaller values.
- The JavaScript behavior/syntax test, plist validation, diff validation, signed device build, and physical-device installation pass.


## October 17, 2026 — unified cards and typography (1.5.9 build 18)

- Today now uses matching cards for Daily nutrition, Meals today, and Movement; redundant Activity and Apple Health headings were removed.
- Journal, Plan, and Progress now share the same lighter page titles, card-title scale, card geometry, supporting text, and button weight.
- The JavaScript behavior/syntax test, plist validation, diff validation, signed device build, and physical-device installation pass.


## October 17, 2026 — illustrated tab introductions (1.6.0 build 19)

- Meal rows now use the nutrition label type scale and green-dot motif.
- Journal and Plan use illustrated purpose cards instead of repeated page-name headings, while Progress opens directly on the seven-day overview.
- This week's notes now uses the approved soft-green overview treatment.
- The JavaScript behavior/syntax test, plist validation, diff validation, signed device build, and physical-device installation pass.


## October 17, 2026 — lighter weekly reflections (1.6.1 build 20)

- Redundant Journal guidance is removed. Saved reflections now use regular sentence text in spacious light tiles inside the soft-green notes card.
- The JavaScript behavior/syntax test, plist validation, diff validation, signed device build, and physical-device installation pass.


## October 17, 2026 — production backend and build 21

- Production FastAPI is live at `https://bitelog-api.vercel.app`; OpenAI configuration is stored only in protected Vercel environment settings.
- Live production checks pass for health, the supplied dietitian PDF, photo meal estimation, and voice meal transcription/estimation.
- BiteLog 1.6.2 build 21 uses the HTTPS backend automatically, migrates existing installs away from the Mac LAN URL, and no longer requests local-network access.
- All 14 backend tests, the iOS JavaScript behavior/syntax test, plist validation, signed device build, physical-device installation, and production error-log scan pass.
- The GitHub remote is still empty because command-line GitHub authentication is missing; the local branch contains the complete history.

## October 18, 2026 — weekly Apple Health totals (1.6.3 build 22)

- Apple Health sync now reads today’s movement plus rolling seven-day totals for active calories, steps, and workout minutes.
- The reviewed weekly update includes those seven-day totals before BiteLog opens the athlete’s email composer.
- If movement has not been synced with the new build, the update asks the athlete to sync from Today instead of presenting a stale one-day snapshot.
- The JavaScript behavior test, plist validation, diff validation, unsigned build, and signed device build pass. Installation on the connected iPhone is still pending because the device connection reset during the first attempt and the retry was not approved.

## October 24, 2026 — App Store Connect upload

- The Apple Developer Program membership for `kanika@themodernhealth.com.au` is active under team `YX8ZU7XXF4` through October 19, 2027.
- BiteLog now uses the Modern Health bundle identifier `au.com.themodernhealth.BiteLog`.
- App Store Connect app record `6826741685` was created with the public name BiteLog and English (Australia) as its primary language.
- BiteLog 1.6.3 build 22 was archived with HealthKit and uploaded successfully. Apple processed it, extracted the BiteLog icon, and marked it Ready to Submit after export compliance was completed.
- A stale Settings footer was corrected, `ITSAppUsesNonExemptEncryption` was added, and corrected build 23 was uploaded for TestFlight processing.
- The exact build 23 archive was installed successfully on Kanika's connected iPhone for final validation.
- External TestFlight distribution to Amie still requires Apple to finish processing build 23, completion of TestFlight information, and Amie's tester email.

## October 25, 2026 — App Store privacy declaration

- App Store Connect privacy responses were corrected and published for BiteLog 1.6.3.
- The public label now declares five data types: Health, Photos or Videos, Audio Data, Other User Content, and Other Diagnostic Data.
- Each declared type is used only for App Functionality, is not linked to the user's identity, and is not used for tracking.
- Incorrect declarations for advertising, interaction tracking, contacts, email messages, crash/performance analytics, Apple Health fitness data kept on device, environment scanning, hands, and head movement were removed.
- Apple removed the privacy-information submission error. Version 1.6.3 build 23 now shows an enabled `Add for Review` button and remains in `Prepare for Submission`; it has not been submitted for public App Review.
