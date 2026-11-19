import { dispatchWorkflow, readConfig } from "./dispatch.mjs";

export default {
  /** Cron trigger entry point. A failure is thrown so Cloudflare records the run as failed and logs the reason. */
  async scheduled(_controller, env) {
    const result = await dispatchWorkflow(readConfig(env));
    console.log(`workflow dispatched (HTTP ${result.status}, ${result.attempts} attempt(s))`);
  },
};
