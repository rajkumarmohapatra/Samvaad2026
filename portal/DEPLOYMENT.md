# Live Samvaad 360 pilot

Verified 28 October 2026.

- Portal: https://samvaad-1xpw.onrender.com
- First administrator setup: https://samvaad-1xpw.onrender.com/setup/
- Sign-in: https://samvaad-1xpw.onrender.com/login/
- Render service: https://dashboard.render.com/web/srv-dbgua0e7bikc7381s8ng
- Source branch deployed by Render: `feat/sambad-360-foundation`
- Neon project: `Samvaad360` (`restless-wildflower-18587355`), Singapore; separate from ISIDIP.

## Create your administrator account

1. Open the Render service dashboard and select Environment.
2. Privately copy the value of `BOOTSTRAP_TOKEN` from that environment. Do not paste it into GitHub or chat.
3. Open the first-administrator setup URL. Enter the setup code, your username/email, and a strong personal password twice.
4. Sign in. Setup stops accepting new administrators after the first superadministrator exists. Remove the bootstrap token from the host after setup when convenient; do not rotate the encryption key casually.
5. Use Administration to create staff users, assign edition Membership records and link participant profiles to participant accounts. There are no shared/default staff passwords.

## Verified

Render deployment `dep-dbgua0u7bikc7381s9bg` reached live with native source commit `7d2d5c0b7713113b0e567b4964b99b9bbb16f308`. Public health/login/setup/static routes responded successfully. Unauthenticated participant access redirected to sign-in. Hosted database counts reconciled to 3,000 current-year and 600 historical synthetic participations, 40 organisational units, and 100 beds. No administrator account was created by the build agent.

35 native server/authentication/domain/template tests and 36 original domain/artifact tests pass locally. GitHub Actions run https://github.com/rajkumarmohapatra/Samvaad2026/actions/runs/40685650350 completed successfully. An authenticated live-browser walkthrough, PostgreSQL concurrency/load certification, backup/restore and remaining enterprise-scope acceptance are not complete.

This is a synthetic pilot on free compute/database plans, not an event-day availability guarantee or a claim of full production readiness. Do not enter real sensitive records yet. See `README.md` in this folder for remaining features and rollout controls. The first visit after inactivity may be slow while the free service starts.

Secrets are stored in Render's environment, not in GitHub. The existing ISIDIP resources were not modified. Future deployment uses the source branch above; changing main alone does not change that service configuration.
