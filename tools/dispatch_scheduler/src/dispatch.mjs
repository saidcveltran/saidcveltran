/**
 * Starts a GitHub Actions workflow through the REST API (`workflow_dispatch`).
 *
 * GitHub's own `schedule` trigger is best effort and did not start at all in the profile repository, so a
 * Cloudflare cron trigger calls this instead. A dispatch is an ordinary API call and is not subject to the
 * scheduler's load shedding. The token never appears in a log line or an error message.
 */

export const API_ROOT = "https://api.github.com";
const API_VERSION = "2022-11-28";
const REPOSITORY_PATTERN = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;
const WORKFLOW_PATTERN = /^[A-Za-z0-9_.-]+\.ya?ml$/;
const BODY_PREVIEW_LIMIT = 200;

export class ConfigError extends Error {
  constructor(problems) {
    super(`Invalid scheduler configuration: ${problems.join("; ")}`);
    this.name = "ConfigError";
  }
}

export class DispatchError extends Error {
  constructor(message) {
    super(message);
    this.name = "DispatchError";
  }
}

/** Reads and validates the Worker's variables and secret. Reports which names are wrong, never their values. */
export function readConfig(env) {
  const problems = [];
  const repository = env.REPOSITORY ?? "";
  const workflow = env.WORKFLOW_FILE ?? "";
  const ref = env.REF ?? "";
  const token = env.GITHUB_DISPATCH_TOKEN ?? "";
  if (!REPOSITORY_PATTERN.test(repository)) problems.push("REPOSITORY must look like owner/name");
  if (!WORKFLOW_PATTERN.test(workflow)) problems.push("WORKFLOW_FILE must be a .yml or .yaml file name");
  if (!ref) problems.push("REF is empty");
  if (!token) problems.push("secret GITHUB_DISPATCH_TOKEN is not set");
  if (problems.length) throw new ConfigError(problems);
  return { repository, workflow, ref, token };
}

function preview(text, token) {
  return text.replaceAll(token, "[token]").replace(/\s+/g, " ").trim().slice(0, BODY_PREVIEW_LIMIT);
}

/**
 * Dispatches the workflow. Retries once on a network error or a 5xx answer, because those are transient;
 * any 4xx answer (bad token, missing workflow, wrong ref) is final and is reported at once.
 * Resolves with { status, attempts }; rejects with DispatchError.
 */
export async function dispatchWorkflow(config, { fetchImpl = fetch, retries = 1, delayMs = 2000, sleep = (ms) => new Promise((done) => setTimeout(done, ms)) } = {}) {
  const url = `${API_ROOT}/repos/${config.repository}/actions/workflows/${config.workflow}/dispatches`;
  const request = {
    method: "POST",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${config.token}`,
      "Content-Type": "application/json",
      "User-Agent": "profile-refresh-scheduler",
      "X-GitHub-Api-Version": API_VERSION,
    },
    body: JSON.stringify({ ref: config.ref }),
  };
  let failure = "no attempt was made";
  for (let attempt = 1; attempt <= retries + 1; attempt += 1) {
    try {
      const response = await fetchImpl(url, request);
      if (response.status === 204) return { status: 204, attempts: attempt };
      const body = preview(await response.text(), config.token);
      failure = `GitHub answered ${response.status} for ${config.repository}/${config.workflow}: ${body}`;
      if (response.status < 500) throw new DispatchError(failure);
    } catch (error) {
      if (error instanceof DispatchError) throw error;
      failure = `network error: ${preview(String(error?.message ?? error), config.token)}`;
    }
    if (attempt <= retries) await sleep(delayMs);
  }
  throw new DispatchError(`${failure} (after ${retries + 1} attempts)`);
}
