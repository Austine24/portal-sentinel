# How to make the 3-minute demo video

**Requirements from the organizers:** at most 3 minutes, shows a real product, shows the core functions, shows Portaldot integration, and has a publicly accessible link. Aim for **2:40 to 2:55**. A judge may stop watching at 3:00.

## Plan the work (about 2 hours)
1. Rehearse twice with a timer, reading `docs/DEMO_SCRIPT.md` (Version A, or Version B if the on-chain record works).
2. Record. 3. Trim and export. 4. Upload and test the link in a private window. 5. Paste the link into the check-in.

**Record Version A first** (no on-chain step). It is safe and you can submit it. If the real on-chain record works before the deadline, record Version B and swap the link in. Never wait for Version B before having Version A uploaded.

## Choose a recorder
- **Easiest: Windows Game Bar.** Press `Win + G`, open Capture, press the record button (or `Win + Alt + R` to start and stop). Turn on the microphone. It records the app window you are in, so keep everything in Chrome and use PowerShell windows as separate recordings if needed.
- **More control: OBS Studio** (free, obsproject.com). Add a "Display Capture" source and your microphone. Output 1080p, MP4.
- **Edit and export:** Clipchamp (built into Windows 11) or the Photos app video editor. Trim mistakes, export 1080p.

## Prepare the screen (10 minutes)
- Start MySQL (Laragon), the backend, and the frontend. Open the Network page once so it shows "connected".
- For a clean take, empty the demo incidents in HeidiSQL: `DELETE FROM incident_events; DELETE FROM incidents;`
- Turn off notifications: `Win + N`, then Focus assist or Do not disturb. Close WhatsApp, Telegram, email.
- Chrome: hide the bookmarks bar (`Ctrl + Shift + B`), zoom to 125 percent (`Ctrl` and `+`), close other tabs, use one clean window.
- Open the terminals you need in the repo root and in `contracts`. Make the font large.
- **Security check:** no `.env` file open, no seed phrase or private key visible anywhere, no password in the terminal history on screen. Your public wallet addresses are fine.

## Recording tips
- Talk slowly. Read short sentences. Pause one second between sections.
- Say "simulated" when showing simulated transactions and "live" when showing the Network page.
- If you stumble, keep going and fix it in editing. If it runs over 3:00, cut the AI page and the status-change click first.
- Quiet room, phone on silent, microphone about a hand's width from your mouth. Do a 10-second test recording and listen to it with headphones.

## Export and upload
1. Export **1080p MP4**.
2. Upload to **YouTube** and set visibility to **Unlisted** (or Public). Title: `Portal Sentinel - Portaldot Hacker House 2026 - Track 3 demo`. Put the GitHub link in the description.
3. **Test the link in a private (incognito) window while logged out.** If it plays there, judges can open it.
4. Paste the link into `docs/CHECKIN_DRAFT.md` and the DoraHacks check-in, and add it to the README.

## What the video must NOT do
- Claim a contract deployment, a transaction hash or an explorer page that is not real.
- Call the transaction data live. The network page is live; the transactions are simulated.
- Say the AI detected an attack or that a wallet is malicious. Say "anomalous" and "requires investigation".
- Leave the node console on the Live network. Select PortaldotV3 Testnet.

## Final-day timetable (UTC)
| When | What |
|---|---|
| Oct 23 | Deploy the contract, record one real piece of evidence, record Version A |
| Oct 24 by 06:00 | Version A uploaded, check-in draft filled in, link tested |
| Oct 24 by 08:00 | **Submit the check-in** (four hours of buffer before the 12:00 deadline) |
| After submitting | If time allows, record Version B and update the link |
