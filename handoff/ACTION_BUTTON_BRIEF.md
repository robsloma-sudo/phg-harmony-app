# Harmony Action Button: brief for the PHG lead agent

- **Prepared:** 2026-10-01 by the previous PHG lead developer, from live logs, live function code and the repo.
- **Requested by:** Rob, who reports: *"The action button is not giving me the same responses that the in-app features are with the new update."*

This brief covers four things:

1. What the Action button is, end to end.
2. Why its answers differ from the app today. The cause is proven from logs.
3. The exact contract between the phone and the server.
4. How to tie the Action button into your update, so the two never drift apart again.

---

## 1. What the Action button is

Rob presses the iPhone Action button. That runs an Apple **Shortcut** called "Harmony". It works from the lock screen, with no app open:

1. Dictate text (listens until he pauses).
2. Show a notification "Thinking…" with the violet orb GIF.
3. POST the words to the Supabase edge function **`phg-harmony-inbox`**.
4. Show a notification with Harmony's reply and the cyan "speaking" orb GIF, then **Speak** the reply aloud.
5. Read `next` from the reply:
   - `listen`: loop back to step 1 (up to 12 turns).
   - `open`: open the URL. iOS requires Face ID or a passcode to leave the lock screen.
   - `end`: stop.

**Rules Rob set (keep them):**

- **The app never opens unless Harmony asks and he says yes.**
  - She asks "Want me to open it in the Harmony app?" and he says "yes".
  - Only then does the reply carry `next:"open"` and a non-empty `url`.
  - Otherwise `url` is always `""`. The link is kept in `app_url`.
- **She can just read things out loud.** "Don't open it, just tell me" returns `read_back`.
- **She asks one narrowing question when a request is open-ended.** Example: "classic, your house version, one from the internet, a few variations, or build one together?"
- **She never answers PHG facts (venues, prices, distilleries, menus) from model memory.** She looks them up first.
- **Stirred drinks are "six to eight seconds".** Never any other stir or shake time unless the spec has one.

**Where the setup lives:**

- In the app: gear → **iPhone Action button**. It is a live, tap-to-copy copy of the finished Shortcut. The code is `scPage()` in `index.html`, around line 41186.
- The same panel issues the personal key: **Create my key** (shown once) and revoke.
- Orb GIFs: `img/harmony-orb-thinking.gif` and `img/harmony-orb.gif`.

---

## 2. The app and the Action button already share ONE brain

| | In-app Harmony view | Action button |
|---|---|---|
| Endpoint | `phg-harmony-inbox` | `phg-harmony-inbox` (same function) |
| Auth | `Authorization: Bearer <user JWT>` + body `account_id` | `x-api-key: hk_…` (SHA-256 looked up in `phg.harmony_device_keys`, which gives user and account) |
| Surface flag | body `surface:"app"` | none, so `via="shortcut"` |
| Conversation memory | app sends `context` (last 6 turns) every call | **the Shortcut must send back the `context` it received** |
| Data lookups | inbox → `phg-harmony-data` | inbox → `phg-harmony-data` server-to-server (`x-phg-internal`) |
| Output | `speak` + `view` (map, card, table) + `voice_first` mp3 | `speak` (iOS speaks it), `next`, `url`, `context` |
| Turn log | `phg.harmony_turns` surface `app` | `phg.harmony_turns` surface `shortcut` |

Live code: `phg-harmony-inbox` platform v35. Its sha `8f03d9…` is byte-identical to `supabase/functions/phg-harmony-inbox/index.ts` in this repo (698 lines, code v29). **It has not changed since 9/29.**

---

## 3. Root cause today (proven from logs)

The edge function logs one line per call: `{"inbox": via, "fields": [...], "turns": N}`. On 2026-10-01:

- **Every app call** sends `fields: ["text","context","surface","account_id","tz","hear","tts"]`. `turns` climbs 0 → 6 as the conversation goes on.
- **Every Action button call** sends `fields: [""]` and `turns: 0` (02:55, 02:55, 04:06 and 18:39 UTC).

`fields: [""]` means the body has one field with an **empty name** holding the dictated words. The server's fallback recovers the words, so she hears him. But **no `context` field is sent**, so every press starts a brand-new conversation.

Rob's phone is running an **old single-shot Shortcut**, not the 18.49.33 loop that round-trips `context`.

Visible symptom in `phg.harmony_turns`:

```
02:55:07 shortcut  "Hey Harmony can you give me a margarita recipes"
          -> "Do you want the classic Margarita, your house margarita, one from the internet, or a few variations?"
02:55:32 shortcut  "A few variations to pick from and the house recipes and the Internet"
          -> "You got it. What drink do you want variations for?"      <- forgot "margarita"
```

In the app, the same flow keeps the thread for 20+ turns (18:23–18:45 UTC).

Other effects of no context:

- `read_back` ("read it again") has nothing to read.
- "Yes, open it" can never open: `context.offered` is never true.
- Corrections ("no, I meant…") have no previous answer to correct.

**Speech repair is skipped too.** Shortcut turns log `hear: null`, so iOS dictation text goes in without PHG's brand-name repair (`phg-speech-transcribe`). The inbox runs a text-only repair for Shortcut text (v17). Check it still runs in your version.

---

## 4. Fix: do both

### 4a. Server-side memory for the Shortcut (no phone change needed; do this first)

In `phg-harmony-inbox`, when `via === "shortcut"` and the request has no `context`:

- Rebuild `ctx.turns` from the database:
  - call `dbx("turns_recent", { user: userId, account: accountId, limit: 6 })`. The op already exists in `public.phg_harmony_inbox_db`, so **no migration is needed**;
  - keep only `surface = 'shortcut'` rows from the **last 10 minutes**;
  - order them oldest first and map them to `{u: user_text, h: reply_text}`.
- Also keep the last result:
  - either add `last` (title/detail/url) and `offered` into `understood` in `turn_log`;
  - or keep a small `phg.harmony_sessions` row keyed by device key (that would need a migration and Rob's OK).
  - Without `last`, `read_back` and "yes, open it" stay limited.
- If the Shortcut *does* send `context`, use it. The client's context wins.

This makes every old Shortcut, Rob's included, behave like the app.

### 4b. Rebuild the Shortcut on the phone (Rob, about 5 minutes)

The correct Shortcut is shown in the app: gear → iPhone Action button. The key points:

- **Get contents of** `https://lqjtwabzmgjcufftuqvu.supabase.co/functions/v1/phg-harmony-inbox`, Method **POST**.
- **Header** `x-api-key` = the personal key.
- **Request Body: JSON** with two fields: `text` = Dictated Text, and `context` = the variable **Context**.
  - Not "Form", and no unnamed field. Today's body has one empty-named field.
- After the call:
  - `speak` → Speak;
  - `context` → set the variable **Context** (this is what carries memory);
  - `next` → If `open`: open `url`. If `end`: stop.
- All of that inside **Repeat 12 times**, with **Context** starting empty before the loop.

Check after rebuilding: the function log for a Shortcut call shows `fields: ["text","context"]`, and `turns` climbs past 0 on the second turn.

---

## 5. Keeping the Action button tied to your update (the rule)

**There must be one conversation brain.** Anything you change in how Harmony thinks, routes or answers in the app must reach the Shortcut path in the same deploy.

1. **If your update changed `phg-harmony-inbox`:**
   - Both surfaces get it automatically.
   - Check every `inApp` / `inAppSurface` / `via === "shortcut"` branch: index.ts lines ~408, 445, 452, 526–537 and 584.
   - In-app-only changes belong in those branches. Everything else stays shared.
2. **If your update moved the app's brain elsewhere** (a new function, a Jev-gated router, the Slack path, Claude instead of OpenAI): `phg-harmony-inbox` must call that same brain for Shortcut turns.
   - Keep the inbox as a thin adapter that does only these jobs:
     - key auth;
     - body parsing (`readBody` accepts JSON, form, multipart and plain text, and recovers unnamed fields);
     - context load and save;
     - the shaping rules for voice-only output: no views, `url` only on `next:"open"`, `app_url` always;
     - the turn log.
   - Do **not** keep a second copy of the prompts, recipe logic or data routing in the inbox. Two copies is exactly how they drift.
3. **Data answers.**
   - The inbox calls `phg-harmony-data` server-to-server. It is now v22, with PHG-086 tier-1 `phg_fast_resolve`.
   - The Shortcut therefore already gets the tier-1 routing, *but only for turns the inbox planner sends to `data`*.
   - If the app now calls `phg-harmony-data` or another service directly for things the inbox handles itself (recipes, notes, menus), the Shortcut won't get them. Route those through the same place.
4. **Jev (`phg-jev`).** It is currently used only in shadow, replay and test (`phg.jev_decisions` surfaces: replay, selftest, accuracy_suite, …). It is not in the live path of either surface. When it goes live:
   - call it from the shared brain, so both surfaces get the same `route` / `guard` / `triage`;
   - pass `surface: "shortcut"`;
   - treat a locked phone as **stricter**: anything Jev marks `proposal_required` or `approval_required` must not run from the Shortcut. Say it, and offer to open the app.
5. **Lessons and feedback.** `phg.harmony_lessons` and `phg.harmony_feedback` should be read and written by the shared brain, so a lesson learned in the app also applies on the phone.
6. **Speech.**
   - The app sends audio to `phg-speech-transcribe`, which does name repair.
   - The Shortcut sends iOS dictation **text**. It must go through the same text-only repair (lexicon plus learned aliases in `phg.harmony_aliases`) before planning.
7. **Voice-only output rules.** These are Shortcut-specific, so keep them:
   - spoken sentences only;
   - no markdown, no lists with symbols, no URLs read aloud;
   - recipes at 60–120 words with exact measures, method, glass and garnish;
   - end with a question only when you need an answer;
   - `next` must be `listen`, `open` or `end`.

---

## 6. Response contract (do not break: the Shortcut on Rob's phone parses these keys)

**Request** (Shortcut):

```
POST /functions/v1/phg-harmony-inbox
x-api-key: hk_…
{ "text": "<dictated words>", "context": "<string from the previous reply, or empty>" }
```

**Response:**

```
{ ok: true,
  speak: "<what to say>",
  next: "listen" | "open" | "end",
  url: "<non-empty ONLY when next == open>",
  app_url: "<link to the same thing in the app>",
  context: "<opaque JSON string: {turns:[{u,h}…6], last:{title,detail,url}, offered:bool}>" }
```

Other actions on the same endpoint (app login only): `add_note`, `list_notes`, `update_note`, `delete_note`, `issue_key`, `list_keys`, `revoke_key`. Also `{warm:true}` to wake it.

---

## 7. How to test without a phone

Do not paste keys into chat or logs.

1. **Issue a temporary key** for Rob's user and account. Call `public.phg_harmony_inbox_db('key_issue', …)` through SQL, as service role. Keep the plaintext only inside the test.
2. **Call the function from SQL with pg_net:**
   - `net.http_post(url, headers {x-api-key}, body {text, context})`;
   - make 3 turns, feeding each reply's `context` into the next call;
   - then repeat the 3 turns with **no** context, to prove 4a works.
3. **Check the result:**
   - turn 2 must remember turn 1, for example "margarita" → "a few variations" lists margarita variations;
   - `phg.harmony_turns` shows surface `shortcut`;
   - `url` stays empty until a yes to an offer.
4. **Revoke and delete the temporary key** (`key_revoke`).
5. Function logs to check: `fields`, `turns`, and the `ms` timings in `understood`.

---

## 8. Shared-brain bugs seen in today's app transcript

These affect both surfaces. Fix them in the shared brain.

1. **Wrong drink repeated three times** (18:37–18:45).
   - Rob asked for "that spec" (his Oaxacan Old Fashioned) three times, and each time got the **plain Old Fashioned** library card.
   - The planner sent it to `data` with a fuzzy drink match; the repair turn (`repair: item`) recognised "Oaxacan Old Fashioned" but the lookup still matched "Old Fashioned".
   - Fix: a drink the user built in this conversation, or a named variant, wins over the base drink. Never answer the base drink when a modifier is present (same rule as the chocolate-Manhattan fix in v12).
2. **False "saved" claim** (18:37).
   - Harmony said "I've added the concise oleo saccharum recipe and ratios to your Oaxacan Old Fashioned spec", but the action was `note`.
   - Only a note was logged. No recipe or house spec was written.
   - She must say "I logged that as a note", or actually save it through the approved recipe-write path (Command Center proposal → approval).
3. **"I do not have a reference spec for Oaxacan Old Fashioned"** (18:28).
   - The data router answered a question about the drink being built *in this conversation* instead of reading the conversation.
   - Questions about "this drink", "our spec" or "the ratio" should read context first.

---

## 9. Files and objects

| What | Where |
|---|---|
| Inbox function (the shared brain + Shortcut door) | `supabase/functions/phg-harmony-inbox/index.ts` (live v35 = repo) |
| Data function | `phg-harmony-data` live v22 (repo copy is older; pull live before editing) |
| DB door | `public.phg_harmony_inbox_db(op, args)`, service_role only. Ops: key_lookup, key_issue, key_list, key_revoke, is_member, notes_*, turn_log, turns_recent, correction_add, aliases_list, alias_upsert, house_recipes |
| Tables | `phg.harmony_device_keys`, `phg.harmony_notes`, `phg.harmony_turns`, `phg.harmony_corrections`, `phg.harmony_aliases`, `phg.harmony_lessons`, `phg.harmony_feedback` |
| Setup page | `index.html` → `scPage()` (about line 41186), gear → iPhone Action button |
| History | `handoff/PHG_RUNNING_CHANGELOG.txt`: entries ACTION, INBOXFIX, SHORTCUTLIVE, INBOXBODY, INBOXFIELD, ASKOPEN, VOICEDATA, CONVERSE, VOICEFIX, CONTEXT, SPEED |
| Platform limits | A Shortcut cannot draw a live overlay or listen while speaking. Barge-in and live visuals need the app or a native iOS app. |

**Order of work:**

1. Do 4a: server-side Shortcut memory.
2. Test it per section 7.
3. Make sure the inbox calls the same brain your update uses (section 5).
4. Fix the section 8 bugs in the shared brain.
5. Rob rebuilds the Shortcut (4b), when convenient.
