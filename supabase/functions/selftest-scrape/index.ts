// selftest-scrape - RETIRED.
//
// This was a one-time diagnostic endpoint used to verify scrape-source end
// to end from a phone browser. It has served its purpose and is now inert:
// no secrets are read, no downstream calls are made, no token is accepted.
//
// Delete this function in the Supabase dashboard (Edge Functions ->
// selftest-scrape -> Delete). Leaving an unauthenticated endpoint deployed,
// even a dead one, is not a habit worth keeping.

Deno.serve(() =>
  new Response(
    JSON.stringify({
      status: "retired",
      message: "Diagnostic endpoint removed. Delete this function in the dashboard.",
    }),
    { status: 410, headers: { "Content-Type": "application/json" } },
  )
);
