# Dev site email (Mailpit)

How email works on the dev site (`http://127.0.0.1:8000`), and what to do when an email doesn't arrive. It does not apply to production.

## What it is for

Several flows send email: a new supplier signing up (the welcome email with the link to set a password), password resets, and account verification links. On dev there is no real mail server, so these emails would never arrive and a tester could not finish creating a login.

Dev therefore sends all email to **Mailpit**, a small local inbox. No message leaves this machine, so seeded or test addresses never receive real mail.

| Part | Where |
|---|---|
| Inbox (read mail here) | http://localhost:8025 |
| Outgoing mail server (SMTP) | `localhost:1025`, no login, no TLS |
| Default outgoing Email Account | "KenTender Dev Mailpit" (in Desk) |
| Mailpit itself | Docker container named `mailpit`, restarts with Docker |
| Sends the queued mail | `make dev-mail-start` (see below) |

Frappe puts email in a queue, and the queue is normally sent by its scheduler. Tender notices to bidders (a clarification answer, an addendum, a deadline change) are also queued and turned into emails by the scheduler. The dev scheduler is switched off on purpose, so a small loop does both jobs instead. It runs only the notice sweep and the mail flush, and no other background job.

## Everyday use

Run these from `apps/kentender_v1/`:

```bash
make dev-mail-start     # send queued mail and queued tender notices every 8 seconds
make dev-mail-status    # loop running? Mailpit up? how many mails waiting?
make dev-mail-stop
```

Start the loop at the beginning of a testing session. It stops when the machine restarts or the terminal that started it is closed, so start it again then.

A new email appears in Mailpit about 10 to 20 seconds after the action (Frappe holds new mail back for about 10 seconds).

### Testing a new supplier

1. Signed out, open a published tender, for example `http://127.0.0.1:8000/tenders/TND-MOH-2027-002`.
2. Choose **New supplier? Create a login** and fill in the name and email.
3. Open http://localhost:8025 and open "Welcome to KenTender".
4. Follow the link in the email and set a password.
5. Sign in. You return to the same tender, where **Set up your supplier account** is offered.

The dev site is reached at `http://127.0.0.1:8000`, never at `kentender.midas.com` (that name is only the site's internal name and does not resolve in a browser). The email links use `http://127.0.0.1:8000` because of the `host_name` setting below.

Sign-ups create real users on the dev site. Remove test users afterwards in Desk (User list).

## Supplier verification links (the Bid Submission test mailbox)

The supplier account's "verify your email" link, and other supplier messages (bid hand-offs, award notices), do not go straight to email on dev. The dev site is a Bid Submission test environment (`kt_bds_simulation_environment`), so these messages are first kept in a private file on the server, `sites/<site>/private/kt_test_mailbox/messages.jsonl`, which a tester cannot open.

The site setting `kt_test_mailbox_also_email` makes the test mailbox also queue each message as an email, so it appears in Mailpit like any other. It is on for dev and off by default, so test sites send nothing.

```bash
bench --site kentender.midas.com set-config kt_test_mailbox_also_email 1
```

Messages created before this was switched on are only in the file. Use **Resend verification link** on the Account page to get a new one in Mailpit.

### When a question is answered

A bidder who asks a question on a tender sees it under **Your questions** (on the tender page and on the bid's Documents screen) as "Received · waiting for an answer". When the procurement officer answers, the answer shows there, and the bidder is told in two ways: an email to the bid's notice address, and a "Your question was answered" link on **My bids**. On dev the email appears in Mailpit about 10 to 20 seconds after the officer answers, as long as `make dev-mail-start` is running. It goes to the notice address chosen when the bid was started, so a mistyped address (for example `hotmal.com`) still shows up in Mailpit, which keeps mail for every address.

## One-time setup on a new machine

1. **Docker in WSL.** Turn on WSL integration in Docker Desktop (Settings, Resources, WSL integration). Add yourself to the docker group, then open a new terminal:
   ```bash
   sudo usermod -aG docker $USER
   ```
2. **If pulling an image fails with "error getting credentials",** remove the Windows credential helper from `~/.docker/config.json` (the line `"credsStore": "desktop.exe"`). Mailpit is public and needs no login.
3. **Start Mailpit:**
   ```bash
   docker run -d --name mailpit --restart unless-stopped -p 1025:1025 -p 8025:8025 axllent/mailpit
   ```
4. **Point the site at it** (from `/home/midasuser/frappe-bench`):
   ```bash
   bench --site kentender.midas.com set-config mail_server localhost
   bench --site kentender.midas.com set-config mail_port 1025
   bench --site kentender.midas.com set-config use_tls 0
   bench --site kentender.midas.com set-config auto_email_id noreply@kentender.local
   bench --site kentender.midas.com set-config disable_mail_smtp_authentication 1
   bench --site kentender.midas.com set-config host_name http://127.0.0.1:8000
   bench --site kentender.midas.com clear-cache
   ```
`host_name` matters: Frappe builds the password link from the site's configured address and ignores the browser's, so without it the link points at `kentender.midas.com`, which does not open.

5. In Desk, add an **Email Account**: outgoing on, **default outgoing**, SMTP server `localhost`, port `1025`, no TLS, no SMTP authentication, email address `noreply@kentender.local`, incoming off.

## When an email does not arrive

Check in this order:

| Check | How | If it fails |
|---|---|---|
| Mailpit is up | `make dev-mail-status`, or open http://localhost:8025 | `docker start mailpit` |
| The loop is running | `make dev-mail-status` | `make dev-mail-start` |
| The supplier verification link is missing | `kt_test_mailbox_also_email` is not set to 1 (see above), or the message predates it | Set it, then use Resend verification link |
| The mail is in the queue | Desk, Email Queue list | If it is missing, the action never sent mail (for example sign-up is switched off, or the user already exists) |
| The link in the email shows `kentender.midas.com` | `host_name` is not set (setup step 4) | Set it, then sign up again or replace the host in the old link with `127.0.0.1:8000` |
| The mail is stuck as "Not Sent" | wait 15 seconds, or `scripts/dev-mail.sh once` | If it stays, open the row and read the error |
| The mail shows "Error" | open the row in Email Queue | Usually Mailpit is down, or the default outgoing Email Account is missing or changed |

If the sign-up page says "Please ask your administrator to verify your sign-up", Frappe could not send the mail. Start with the checks above.

## Related

- The Bid Submission module's **Test Mailbox** (Bid Submission runbook, section 3) is described above. Frappe's own login emails (sign-up welcome, password reset) do not use it; they go to Mailpit directly.
- Website sign-up is switched on by the migration `bds_v08_enable_supplier_signup` in `kentender_suppliers`. If the login page shows no "Sign up" link, run `make migrate`.
