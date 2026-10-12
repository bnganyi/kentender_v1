# Bidder workspace: Mailpit quick start

Dev only. Mailpit is a local inbox that catches every email the dev site sends, so you can complete bidder sign-up, verification and login without a real mail server. Nothing leaves your machine.

Full detail and troubleshooting: [DEV_MAIL_RUNBOOK.md](DEV_MAIL_RUNBOOK.md).

## 1. One-time setup (skip if already done on your machine)

**Docker in WSL.** Enable WSL integration in Docker Desktop, then `sudo usermod -aG docker $USER` and open a new terminal. If an image pull fails with "error getting credentials", delete the `"credsStore": "desktop.exe"` line from `~/.docker/config.json`.

**Start Mailpit:**

```bash
docker run -d --name mailpit --restart unless-stopped -p 1025:1025 -p 8025:8025 axllent/mailpit
```

**Point the site at it** (from your bench root, the folder that contains `apps/` and `sites/`; set `SITE` to your own site's name):

```bash
SITE=kentender.midas.com
bench --site $SITE set-config mail_server localhost
bench --site $SITE set-config mail_port 1025
bench --site $SITE set-config use_tls 0
bench --site $SITE set-config auto_email_id noreply@kentender.local
bench --site $SITE set-config disable_mail_smtp_authentication 1
bench --site $SITE set-config host_name http://127.0.0.1:8000
bench --site $SITE set-config kt_test_mailbox_also_email 1
bench --site $SITE clear-cache
```

- `host_name` makes the links in emails open at `127.0.0.1:8000`. Without it they point at `kentender.midas.com`, which does not resolve.
- `kt_test_mailbox_also_email` is what puts the supplier **verification link** into Mailpit.

**Add an outgoing Email Account in Desk** (Email Account list, New): tick **Enable Outgoing** and **Default Outgoing**, SMTP server `localhost`, port `1025`, no TLS, no SMTP authentication, address `noreply@kentender.local`, incoming off.

## 2. Every session

Run from `apps/kentender_v1/`:

```bash
make dev-mail-start     # the dev scheduler is off; this sends queued mail every 8 s
make dev-mail-status    # loop running? Mailpit up? mails waiting?
```

The script finds your bench root from its own location and assumes the site is `kentender.midas.com`. If your site has another name, pass it: `SITE=your.site make dev-mail-start`. If your bench is somewhere unusual, also pass `BENCH_ROOT=/path/to/bench`.

Restart `make dev-mail-start` after a reboot or when the terminal that started it is closed. Inbox: **http://localhost:8025**.

Always browse the dev site at **http://127.0.0.1:8000**, never `kentender.midas.com`.

## 3. The registration and login walk

1. Signed out, open a published tender, for example `http://127.0.0.1:8000/tenders/TND-MOH-2027-002`.
2. Choose **New supplier? Create a login**. Enter a name and an email. Any address works, because Mailpit keeps mail for every address.
3. Open Mailpit and open **Welcome to KenTender**. Allow 10 to 20 seconds.
4. Follow the link and set a password.
5. Sign in. You return to the same tender, which now offers **Set up your supplier account**.
6. On the Account page, enter the organisation details. The page then shows **Pending verification**.
7. Open Mailpit for the verification email and follow its link. If it is missing, use **Resend verification link** on the Account page.
8. You can now start a bid and reach **My bids**.

To repeat the walk, use a new email each time (the same address cannot sign up twice), or delete the test user in Desk (User list).

Other emails you can trigger from the bidder side: password reset ("Forgot password?" on the login page), and "Your question was answered" (a bidder asks a question on a tender; a procurement officer answers it).

## 4. If an email does not arrive

| Check | Fix |
|---|---|
| `make dev-mail-status` shows the loop stopped | `make dev-mail-start` |
| `cd: /home/midasuser/frappe-bench: No such file` | Pull the latest `scripts/dev-mail.sh`, or run `BENCH_ROOT=/path/to/bench make dev-mail-start` |
| Mailpit shows down | `docker start mailpit` |
| Verification link never arrives | Confirm `kt_test_mailbox_also_email` is 1, then use **Resend verification link** (older messages are not re-sent) |
| Link shows `kentender.midas.com` | Set `host_name` (section 1), then sign up again, or swap the host in the link for `127.0.0.1:8000` |
| Mail stuck "Not Sent" in Desk's Email Queue | Wait 15 s, or run `scripts/dev-mail.sh once` |
| Mail shows "Error" | Open the row and read it; usually Mailpit is down or the default outgoing Email Account is missing |
| No "Sign up" link on the login page | Run `make migrate` (the migration `bds_v08_enable_supplier_signup` switches sign-up on) |
