# OpenClaw hardening checklist

A short, practical checklist for people who run their own [OpenClaw](https://github.com/openclaw/openclaw) agent. Every item links back to the official OpenClaw docs, which are the source of truth. If the docs and this list ever disagree, follow the docs and [open an issue](../../issues) here.

> **Scope.** This is a checklist, not a guarantee. Working through it reduces common risks. It doesn't make any setup "safe", and it doesn't replace OpenClaw's own `openclaw security audit`. Last checked against the docs on **18 Oct 2026**.

**Who wrote this.** Disclosure: this is posted by an AI agent on behalf of Is My Agent Safe (ismyagentsafe.com), run by Your Evenings Ltd. It was drafted by an AI agent and checked against the linked documentation. Corrections are welcome, and so are pull requests.

---

## 0. Start with the built-in audit

OpenClaw ships its own audit. Run it after any config change, and before exposing anything to a network. ([docs: `openclaw security`](https://docs.openclaw.ai/cli/security), [running the audit](https://docs.openclaw.ai/gateway/security/running-the-audit))

```bash
openclaw security audit            # config, filesystem and read-only checks
openclaw security audit --deep     # adds best-effort live Gateway checks and plugin-owned collectors
openclaw security audit --json     # machine-readable output
openclaw security audit --fix      # applies a narrow set of automatic repairs
```

- [ ] I ran `openclaw security audit --deep` and read every **critical** finding. (The audit output doesn't include your version. Check it separately with `openclaw --version`; see section 1.)
- [ ] I know what `--fix` does and doesn't do. **It does:** flip open group policies to allowlists and tighten file permissions. **It does not:** rotate tokens or API keys, disable tools, change the gateway bind, auth or network exposure, or remove plugins and skills. ([docs](https://docs.openclaw.ai/cli/security))
- [ ] If I use `security.audit.suppressions`, each one has a written reason. Suppressed findings disappear from the summary, but they stay in the JSON output under `suppressedFindings`.

The docs give this **fix order** ([running the audit](https://docs.openclaw.ai/gateway/security/running-the-audit)):

1. anything "open" with tools enabled
2. public network exposure
3. remote browser control
4. file permissions
5. plugins

## 1. Stay up to date

- [ ] I know my version: `openclaw --version`.
- [ ] I'm on the latest stable release (`openclaw --version`), and I checked the [OpenClaw security advisories](https://github.com/openclaw/openclaw/security/advisories) for my version. For reference:
  - **Floor for the Gateway/CLI: 2026.8.1** ([release](https://github.com/openclaw/openclaw/releases/tag/v2026.8.1), Aug 31, 2026). It fixed 48 advisories, 17 of them high severity, for example [GHSA-ghpx-6xwq-2w4w](https://github.com/openclaw/openclaw/security/advisories/GHSA-ghpx-6xwq-2w4w). As of Oct 18, 2026, no high-severity Gateway/CLI advisory lists a later fix. Later releases still carry medium fixes, so treat 2026.8.1 as a floor, not a target.
  - Older: [CVE-2026-25253](https://nvd.nist.gov/vuln/detail/CVE-2026-25253) ([GHSA-g8p2-7wf7-98mq](https://github.com/openclaw/openclaw/security/advisories/GHSA-g8p2-7wf7-98mq), high). Versions before 2026.1.29 took a `gatewayUrl` value from a query string and connected to it automatically, without prompting, sending the auth token. A crafted link could hand the token to an attacker (1-click RCE). Fixed in **2026.1.29**.
- [ ] **If I use the OpenClaw iOS app:** it's on **2026.8.11** or later. That's an iOS app version, not a Gateway release. [GHSA-jjpc-p3xf-8g7p](https://github.com/openclaw/openclaw/security/advisories/GHSA-jjpc-p3xf-8g7p) (high): before 2026.8.11, the app's Terminal and session Dashboard views didn't enforce a saved Gateway TLS pin, so a spoofed page could read the Gateway token or password. The Gateway software itself isn't affected, but its credentials are. If I used those views on an untrusted network before upgrading, I rotate the Gateway token or password.
- [ ] Before upgrading, I preview it with `openclaw update --dry-run` and read the release notes for breaking changes. ([docs: `openclaw update`](https://docs.openclaw.ai/cli/update))

## 2. Keep the Gateway private

The Gateway serves WebSocket and HTTP, including the Control UI, on one port (default **18789**). ([network exposure](https://docs.openclaw.ai/gateway/security/network-exposure))

- [ ] `gateway.bind` is `"loopback"`, the default on a regular host install. **Container images default to an exposed bind**, so pair them with auth and a firewall. ([security overview](https://docs.openclaw.ai/gateway/security), [exposure runbook](https://docs.openclaw.ai/gateway/security/exposure-runbook))
- [ ] To reach it remotely, I use **Tailscale Serve** or an SSH tunnel, not a LAN bind or port forwarding. If I must bind beyond loopback, I firewall the port to a tight source-IP allowlist. The docs say: never expose the Gateway unauthenticated on `0.0.0.0`.
- [ ] Gateway auth is set (`gateway.auth.mode: "token"` is recommended). The token is a real random secret, e.g. `openssl rand -hex 32` or `openclaw doctor --generate-gateway-token`. The audit flags blank tokens as critical and warns under 24 characters.
- [ ] `gateway.auth.mode` is **not** `"none"`. That setting leaves Gateway HTTP APIs reachable without a shared secret.
- [ ] **Docker on a VPS:** published ports bypass ordinary host firewall rules. I enforce rules in the `DOCKER-USER` chain, as the docs describe. Then I check from outside with `nmap -sT -p 1-65535 <public-ip> --open`, and only the ports I meant to expose are open.
- [ ] **Behind a reverse proxy:** `gateway.trustedProxies` is set narrowly, `gateway.allowRealIpFallback` stays `false`, and the proxy **overwrites** `X-Forwarded-For` rather than appending to it.
- [ ] **Control UI off loopback:** it's served over HTTPS, and `gateway.controlUi.allowedOrigins` is never `["*"]`.
- [ ] **mDNS/Bonjour:** `discovery.mdns.mode` is `"minimal"` or `"off"`, not `"full"`, which leaks the CLI path and SSH port. Or set `OPENCLAW_DISABLE_BONJOUR=1`.

## 3. Decide who can talk to your agent

([access control](https://docs.openclaw.ai/gateway/security/access-control), [hardened baseline](https://docs.openclaw.ai/gateway/security/hardened-baseline))

- [ ] DMs use pairing (`dmPolicy: "pairing"`), and group chats need a mention (`requireMention: true`).
- [ ] DM and sender allowlists have no `"*"` entries. (An open DM policy needs `"*"` as an explicit opt-in, so `"*"` there means anyone can message the agent.) Group policies are `allowlist`, not `open`. A `"*"` group default is only reasonable together with `requireMention: true`, which is how the docs' hardened baseline uses it.
- [ ] If more than one person can DM the agent: `session.dmScope: "per-channel-peer"`. The docs say this is cooperative hardening, **not isolation between people who don't trust each other**. Use separate gateways for that.
- [ ] Channel allowlists use stable IDs, not names or emails. The audit warns when they rely on mutable names.

## 4. Limit what the agent can do

([tool and agent permissions](https://docs.openclaw.ai/gateway/security/tool-permissions), [sandboxing](https://docs.openclaw.ai/gateway/sandboxing))

- [ ] For any agent that reads untrusted content (email, web, group chats), these tools are denied: `gateway`, `cron`, `sessions_spawn`, `sessions_send`.
- [ ] `tools.elevated` (exec outside the sandbox) is off, or `allowFrom` is tightly limited.
- [ ] Agents that don't need my files use the sandbox (`agents.defaults.sandbox`). Sandboxing is **off by default**, and the docs note it isn't a perfect boundary. `workspaceAccess` is `"none"` or `"ro"` unless the agent needs to write.
- [ ] Filesystem tools are limited to the workspace (`tools.fs.workspaceOnly: true`). No agent workspace is set to my whole home directory.
- [ ] If I use a small model with web or browser tools, it's sandboxed. The audit warns about models of 300B parameters or fewer that run without a sandbox and with web or browser tools.
- [ ] I've read the [prompt injection](https://docs.openclaw.ai/gateway/security/prompt-injection) page. Any content the agent reads can try to steer it.

## 5. Treat skills and plugins as code you run

([tool permissions: plugins and skills](https://docs.openclaw.ai/gateway/security/tool-permissions))

- [ ] I only install plugins and skills from sources I trust. Plugins run **in-process with the Gateway**, and skill folders count as trusted code.
- [ ] There's an explicit `plugins.allow` list, and plugin versions are pinned exactly (`@scope/pkg@1.2.3`).
- [ ] I don't use `--force` just to get past an install warning. (`--force` confirms provenance; it doesn't bypass `security.installPolicy`.)
- [ ] I removed plugins and skills I don't use.

## 6. Protect secrets on disk and in logs

([secrets, storage and logs](https://docs.openclaw.ai/gateway/security/secrets-and-storage))

- [ ] `~/.openclaw` is `700` and `~/.openclaw/openclaw.json` is `600`. (`openclaw doctor` and `openclaw security audit --fix` can tighten these.)
- [ ] I assume everything under `~/.openclaw/` may hold secrets: config tokens, `credentials/**`, the agent SQLite databases with model auth profiles and transcripts, and `secrets.json` if used.
- [ ] Provider API keys live in the Gateway process environment, `~/.openclaw/.env` or SecretRefs, not in a workspace `.env`. OpenClaw blocks provider keys from untrusted workspace `.env` files.
- [ ] Session transcripts can contain pasted secrets. I prune old transcripts and logs, and share `openclaw status --all` (redacted) rather than raw logs.
- [ ] The host has full-disk encryption. On a shared host, the Gateway runs as its own OS user.
- [ ] No `dangerous*` or `dangerously*` settings are on in production. The audit reports them under `config.insecure_or_dangerous_flags`. ([full list](https://docs.openclaw.ai/gateway/security/network-exposure))

## 7. Cap the bill (general advice: check your provider's docs)

- [ ] Each app or agent has **its own** API key, so a leak can be revoked without breaking everything else. Spend caps usually live at the account or project level, not on the key. OpenAI, for example, sets [hard spend limits](https://developers.openai.com/api/docs/guides/spend-limits) as monthly amounts per organization or project. To cap one agent, give it its own project with a hard limit. Spend alerts only notify and don't stop traffic, and OpenAI notes recorded spend can slightly exceed a hard limit. Other providers differ, so check their docs.
- [ ] I've checked how often the heartbeat runs and which model it uses ([heartbeat docs](https://docs.openclaw.ai/gateway/heartbeat)). A frequent heartbeat on a premium model costs money even when nothing happens.

## 8. If you think something went wrong

These steps come from the docs' [operator incident response](https://docs.openclaw.ai/gateway/security/operator-incident-response):

1. **Contain:** stop the Gateway, set `gateway.bind: "loopback"` (or turn off Tailscale Funnel/Serve), and set risky DMs and groups to `dmPolicy: "disabled"`.
2. **Rotate:** rotate the Gateway token/password, then remote client secrets, then provider and channel credentials. Assume compromise if secrets leaked.
3. **Audit:** check `openclaw logs` and the relevant transcripts, review recent changes to bind, auth, policies, `tools.elevated` and plugins, and re-run `openclaw security audit --deep`.
4. **Report:** OpenClaw's [security policy](https://github.com/openclaw/openclaw/security) explains how to report a vulnerability.

---

Want the audit output explained in plain English? Is My Agent Safe has a free check (paste your `openclaw security audit --deep` output, plus `openclaw --version` for the version check): <https://ismyagentsafe.com/check?utm_source=github&utm_medium=referral&utm_campaign=evergreen&utm_content=hardening-checklist>

Not affiliated with or endorsed by the OpenClaw project. Licensed under [CC BY 4.0](LICENSE).
