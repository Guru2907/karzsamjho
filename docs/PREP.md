# PREP.md: what Team Y2K Devs prepared before the hackathon

COLOSSUS 3.0 allows up to 20-25% preparation before the start. This file lists everything we did before 11:30 AM on 13 Nov 2026. No product code was written before the start: this repository was created at 11:30 AM on 13 Nov, and its commit history shows all development.

## 1. Planning and documents
| What | When |
|---|---|
| Round 1 idea deck (KarzSamjho, FinTech track) | Submitted for Round 1 |
| Team handbook: scope, API contract, clock plan, test plan, demo script | 10-13 Nov |
| CLAUDE.md, AGENTS.md, docs/TASKS.md (instructions and task list for AI coding tools; plain text, no code) | 13 Nov |

## 2. Accounts and keys
| Service | What we did | When |
|---|---|---|
| Telegram | Created two bots with BotFather (demo and test) | 11-13 Nov |
| Google AI Studio (Gemini) | Created a free-tier API key | 11-13 Nov |
| Groq | Created a free-tier API key | 11-13 Nov |
| Bhashini | Started registration; not used (needs institutional approval) | 10 Nov |

## 3. Throwaway test scripts (in prep/, not part of the product)
| Script | Purpose |
|---|---|
| prep/test_keys.py | Calls each service once to prove the key works; prints PASS/FAIL and seconds |
| prep/tg_test.py | Proves the bot can receive a photo and send back fixed text + an MP3 |

Results of prep/test_keys.py on 13 Nov 2026, about 02:30 AM IST:
| Service | Result | Seconds |
|---|---|---|
| Telegram demo bot / test bot | PASS | 4.9 / 4.3 |
| Gemini 3.5 Flash-Lite (image) | PASS | 8.4 |
| Gemini 3.8 Flash | FAIL (503, high demand) | - |
| Gemma 4 31B | FAIL (503, high demand) | - |
| Groq Qwen vision | PASS | 1.4 |
| Groq gpt-oss-20b | PASS | 1.1 |
| edge-tts Hindi | PASS | 3.3 |
| Groq Whisper | PASS | 0.8 |

prep/tg_test.py on 13 Nov, 02:40 AM IST: PASS (photo in, fixed text + MP3 out).

## 4. Data prepared
Fill in before the first commit; delete any line that does not apply.
| What | Status | When | By |
|---|---|---|---|
| RBI directory of digital lending apps saved as rbi_dla.csv | (fill in) | | |
| 30 synthetic loan ads (images) + expected answers | (fill in) | | |
| 10 synthetic harassment samples + expected rules | (fill in) | | |
| 3 demo ads printed on paper | (fill in) | | |
| 1 generated sample ad (sample_ad.jpg, made by prep/test_keys.py) | Done | 13 Nov | |

## 5. Design
| What | Status |
|---|---|
| Rough wireframe of the card and the 4 routes | (fill in) |
| UI component library and hero style chosen (shadcn/ui; split hero) | Chosen, nothing built |

## 6. Environment
Python, Node.js, Git and editors installed on team laptops; Python packages downloaded once in prep/ to warm the cache.

## 7. Not done before the start
No bot, API, maths, web pages, PDF code, prompts or designs from the product were written before 11:30 AM on 13 Nov. Nothing was copied from earlier projects.

## 8. Tools and credits
AI coding tools used during the event: Claude Code, Cursor. Outside services: Telegram Bot API, Groq (Qwen, gpt-oss-20b, Whisper), Google Gemini API, edge-tts. Libraries: FastAPI, Pydantic, RapidFuzz, ReportLab, python-telegram-bot, React, Vite, Tailwind, shadcn/ui, lucide-react.

## Agent context files (planning, written before 11:30 AM; copied into the repo at A1)
CLAUDE.md, AGENTS.md, docs/TASKS.md, README.md, .env.example, .gitignore, docs/PROGRESS.md, docs/DECISIONS.md, docs/ARCHITECTURE.md, docs/TESTING.md, docs/DEMO.md, docs/RUNBOOK.md. No product code.
