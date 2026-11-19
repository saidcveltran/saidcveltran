# Profile refresh scheduler

A Cloudflare Worker whose only job is to start the profile's refresh workflow every 15 minutes.

GitHub's `schedule` trigger is best effort: it may be delayed, dropped under load, and in a new private
repository it did not start at all (no scheduled run in more than three hours; the same is reported in
[community discussion 213230](https://github.com/orgs/community/discussions/213230)). A Cloudflare cron
trigger calls the GitHub REST API `workflow_dispatch` endpoint instead, which is an ordinary API call and
works (manual dispatches succeed).

## Files

| File | Purpose |
| --- | --- |
| `src/dispatch.mjs` | Validates the configuration and sends the dispatch; one retry on a network error or 5xx, none on 4xx |
| `src/index.mjs` | The cron entry point; throws on failure so the run shows as failed in Cloudflare |
| `wrangler.jsonc` | Name, cron `*/15 * * * *`, variables (repository, workflow file, ref); no route and no workers.dev address |
| `test/dispatch.test.mjs` | 14 offline tests with a fake `fetch` (no network, no real token) |

## Credential

One secret, `GITHUB_DISPATCH_TOKEN`: a fine-grained personal access token limited to the profile repository,
with only **Actions: Read and write** (plus the implicit read-only metadata). It can start workflows in that
one repository and nothing else. It is set with `wrangler secret put GITHUB_DISPATCH_TOKEN` and is never written
to a file, a log line or an error message (the tests check the last two).

## Use

```
npm test                      # offline tests, Node 24
npx wrangler@4.159.0 deploy   # needs CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID
```

When the profile moves to the repository `saidcveltran/saidcveltran`, change `REPOSITORY` in `wrangler.jsonc`,
issue a new token for that repository, and deploy again.
