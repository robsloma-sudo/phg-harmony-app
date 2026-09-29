# Harmony feedback review (start of every session with Rob)

Rob, 2026-09-29: "every time someone says no or that's wrong, or Harmony can't find the answer, or the error screen
comes up - log it, so when I come back we get a log of what's not working and teach the model to do better."

## What is captured (phg.harmony_feedback)
| kind | captured by | when |
|---|---|---|
| no_answer | DB trigger on phg.harmony_turns + phg-harmony-data | Harmony replied "couldn't work that out / could not answer / no results / I don't know", or the SQL gateway failed |
| user_disagreed | DB trigger on phg.harmony_turns | the user's next words were a correction ("no", "that's wrong", "can't be right", "we have over ...", is_correction) - logs the question + wrong answer + what the user said back |
| user_flagged | app "Not right?" button under every Harmony answer card | tap |
| empty_result | phg-harmony-data | a source or the SQL path returned an empty view |
| error | phg-harmony-data | planner could not plan, a source threw ("Could not load"), ask path crashed |
| client_error | app | the request to Harmony failed (network / HTTP error) |

Every conversation turn is also in phg.harmony_turns; every generated SQL in phg.harmony_query_log.

## Review (run these)
```sql
-- open items, newest first
select * from phg.v_harmony_feedback_open;
-- grouped
select kind, source, count(*) from phg.harmony_feedback where status = 'new' group by 1, 2 order by 3 desc;
-- the SQL Harmony wrote around a failure
select at, sql, error, row_count from phg.harmony_query_log where at > now() - interval '7 days' order by at desc;
```

## Fix loop
1. For each open item: find the cause (wrong source chosen, missing source, bad SQL, missing data, wording not understood).
2. Fix it the cheapest durable way:
   - a **lesson** (no deploy; read by the planner / SQL writer on every request, cached 2 min):
     `insert into phg.harmony_lessons (scope, lesson, from_feedback) values ('planner'|'sql'|'conversation', '<rule>', <feedback id>);`
   - a fastPlan pattern or a new source in supabase/functions/phg-harmony-data/index.ts (deploy);
   - data (load what is missing).
3. Close it: `update phg.harmony_feedback set status='fixed', fix_notes='...', lesson_id=..., reviewed_at=now() where id in (...);`
   (`wontfix` / `duplicate` for the rest.)
4. Log the round in handoff/PHG_RUNNING_CHANGELOG.txt.

## Log so far
- #1-#2 (2026-09-29 17:00-17:02): "how many liquor licenses do we have" -> 1,284 then 4,341 (it counted menu venues in
  mv_drink_explorer); "the number is 28,855, do you see it?" -> Could not answer. Cause: the licenses source was not
  deployed yet. Fix: licenses source (phg-harmony-data v14) + lessons #1 (planner) and #2 (sql).
- Round 1 closed 2026-09-29: #1 fixed (28,855 = "Venue universe" = v_public_stats venues NY 16,633 + CO 7,540 +
  IA 4,682; lessons 3-4), #2 fixed (licences != menu venues; licenses source + lessons 1-2).
- Round 2 (2026-09-29 18:0x, lead developer): #4/#6 "active on-premise licences in Dallas / Houston" -> "No licences",
  #5 = Rob's "Not right?" tap on it (duplicate). Cause: the planner passed "on-premise" as the licence type, which
  filters to 0 rows. Fix: phg_license_venues ignores generic words (active/on-premise/liquor/licence/venue);
  planner lesson #5. Houston now returns 2,000+ venues and Dallas 1,820.
  NOTE: the first routine run (17:55) had no Supabase tools in its session, so it could not read the log. The routine
  needs the Supabase connector attached.
