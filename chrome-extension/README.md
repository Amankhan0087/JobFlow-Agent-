# JobFlow Agent — Chrome Extension

1-click add any job to your JobFlow pipeline directly from LinkedIn, Indeed, Glassdoor, Bayt, Reed, StepStone, NaukriGulf, GulfTalent, or Tanqeeb.

## Install (Developer Mode)

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Select this `chrome-extension/` folder
5. Pin the extension to your toolbar

## Features

- **⚡ Add to JobFlow button** — injected on all supported job boards
- **Popup dashboard** — live stats (applied, interviews, offers, jobs found)
- **Quick actions** — trigger Scrape / Match Score / Auto Apply / Follow Up from popup
- **API health indicator** — green/red dot shows if backend is running
- **Duplicate detection** — won't add the same job twice

## Supported Platforms

| Platform | Countries |
|---|---|
| LinkedIn | UAE, UK, SA, Germany, USA |
| Indeed | UAE, UK, SA, Germany, USA |
| Glassdoor | USA |
| Bayt | UAE, SA |
| Reed | UK |
| StepStone | Germany |
| NaukriGulf | UAE, SA |
| GulfTalent | UAE, SA |
| Tanqeeb | SA |

## Requirements

JobFlow backend must be running:
```bash
python -m uvicorn jobflow.api.main:app --reload --port 8000
```
