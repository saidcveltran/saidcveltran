import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { ConfigError, DispatchError, dispatchWorkflow, readConfig } from "../src/dispatch.mjs";
import scheduler from "../src/index.mjs";

const TOKEN = "synthetic-test-credential-0001";
const ENV = { REPOSITORY: "owner/profile", WORKFLOW_FILE: "profile-data-refresh.yml", REF: "main", GITHUB_DISPATCH_TOKEN: TOKEN };
const CONFIG = readConfig(ENV);
const instant = { sleep: async () => {}, delayMs: 0 };

/** A fetch double that answers from a script and records every call. */
function scripted(...answers) {
  const calls = [];
  const fetchImpl = async (url, init) => {
    calls.push({ url, init });
    const answer = answers[Math.min(calls.length - 1, answers.length - 1)];
    if (answer instanceof Error) throw answer;
    return new Response(answer.body ?? null, { status: answer.status });
  };
  return { fetchImpl, calls };
}

describe("readConfig", () => {
  it("accepts a complete configuration", () => {
    assert.deepEqual(CONFIG, { repository: "owner/profile", workflow: "profile-data-refresh.yml", ref: "main", token: TOKEN });
  });

  it("names every missing or malformed setting and never echoes a value", () => {
    const wrong = { REPOSITORY: "not-a-repository", WORKFLOW_FILE: "../evil.sh", REF: "", GITHUB_DISPATCH_TOKEN: "" };
    assert.throws(() => readConfig(wrong), (error) => {
      assert.ok(error instanceof ConfigError);
      for (const name of ["REPOSITORY", "WORKFLOW_FILE", "REF", "GITHUB_DISPATCH_TOKEN"]) assert.match(error.message, new RegExp(name));
      assert.doesNotMatch(error.message, /evil/);
      return true;
    });
  });

  it("rejects a path-like workflow name so the URL cannot be redirected", () => {
    assert.throws(() => readConfig({ ...ENV, WORKFLOW_FILE: "a/../../b.yml" }), ConfigError);
    assert.throws(() => readConfig({ ...ENV, REPOSITORY: "owner/profile/extra" }), ConfigError);
  });

  it("requires the secret", () => {
    const { GITHUB_DISPATCH_TOKEN: _omitted, ...withoutSecret } = ENV;
    assert.throws(() => readConfig(withoutSecret), /GITHUB_DISPATCH_TOKEN/);
  });
});

describe("dispatchWorkflow", () => {
  it("posts the ref to the workflow's dispatch endpoint with the token and succeeds on 204", async () => {
    const { fetchImpl, calls } = scripted({ status: 204 });
    const result = await dispatchWorkflow(CONFIG, { fetchImpl, ...instant });
    assert.deepEqual(result, { status: 204, attempts: 1 });
    assert.equal(calls.length, 1);
    assert.equal(calls[0].url, "https://api.github.com/repos/owner/profile/actions/workflows/profile-data-refresh.yml/dispatches");
    assert.equal(calls[0].init.method, "POST");
    assert.equal(calls[0].init.headers.Authorization, `Bearer ${TOKEN}`);
    assert.deepEqual(JSON.parse(calls[0].init.body), { ref: "main" });
  });

  it("retries once after a 502 and then succeeds", async () => {
    const { fetchImpl, calls } = scripted({ status: 502 }, { status: 204 });
    assert.deepEqual(await dispatchWorkflow(CONFIG, { fetchImpl, ...instant }), { status: 204, attempts: 2 });
    assert.equal(calls.length, 2);
  });

  it("retries once after a network error", async () => {
    const { fetchImpl, calls } = scripted(new TypeError("fetch failed"), { status: 204 });
    assert.equal((await dispatchWorkflow(CONFIG, { fetchImpl, ...instant })).attempts, 2);
    assert.equal(calls.length, 2);
  });

  it("gives up after the retry budget on a persistent 5xx", async () => {
    const { fetchImpl, calls } = scripted({ status: 503, body: "unavailable" });
    await assert.rejects(dispatchWorkflow(CONFIG, { fetchImpl, ...instant }), /503.*after 2 attempts/);
    assert.equal(calls.length, 2);
  });

  it("does not retry a 4xx: a wrong token or workflow will not fix itself", async () => {
    for (const status of [401, 403, 404, 422]) {
      const { fetchImpl, calls } = scripted({ status, body: "Bad credentials" });
      await assert.rejects(dispatchWorkflow(CONFIG, { fetchImpl, ...instant }), (error) => error instanceof DispatchError && error.message.includes(String(status)));
      assert.equal(calls.length, 1, `status ${status}`);
    }
  });

  it("never leaks the token, even when the API echoes it back", async () => {
    const { fetchImpl } = scripted({ status: 401, body: `bad credentials: ${TOKEN}` });
    await assert.rejects(dispatchWorkflow(CONFIG, { fetchImpl, ...instant }), (error) => {
      assert.ok(!error.message.includes(TOKEN));
      assert.match(error.message, /\[token\]/);
      return true;
    });
    const { fetchImpl: failing } = scripted(new Error(`connect failed for ${TOKEN}`));
    await assert.rejects(dispatchWorkflow(CONFIG, { fetchImpl: failing, ...instant }), (error) => !error.message.includes(TOKEN));
  });

  it("keeps a long error body short", async () => {
    const { fetchImpl } = scripted({ status: 400, body: "x".repeat(5000) });
    await assert.rejects(dispatchWorkflow(CONFIG, { fetchImpl, ...instant }), (error) => error.message.length < 400);
  });
});

describe("scheduled handler", () => {
  it("fails loudly when the configuration is wrong, before any request is made", async () => {
    const original = globalThis.fetch;
    let called = false;
    globalThis.fetch = async () => { called = true; return new Response(null, { status: 204 }); };
    try {
      await assert.rejects(scheduler.scheduled({}, { ...ENV, GITHUB_DISPATCH_TOKEN: "" }), ConfigError);
      assert.equal(called, false);
    } finally {
      globalThis.fetch = original;
    }
  });

  it("dispatches with the configured workflow", async () => {
    const original = globalThis.fetch;
    const urls = [];
    globalThis.fetch = async (url) => { urls.push(url); return new Response(null, { status: 204 }); };
    try {
      await scheduler.scheduled({}, ENV);
      assert.equal(urls.length, 1);
      assert.match(urls[0], /owner\/profile\/actions\/workflows\/profile-data-refresh\.yml\/dispatches$/);
    } finally {
      globalThis.fetch = original;
    }
  });

  it("exposes no HTTP handler", () => {
    assert.equal(scheduler.fetch, undefined);
  });
});
