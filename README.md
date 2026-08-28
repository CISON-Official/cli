# CISON CLI

A command-line interface for automating CISON administrative workflows — querying member and payment data, generating membership certificates, managing Zoho Campaigns email/mailing-list operations, and sending bulk notifications — all from the terminal.

## Features

- **Member management** — look up users by member ID or user ID, search the full user database, and export members grouped by Nigerian state.
- **Payment tracking** — export users with no, partial, or complete payments in CSV, JSON, XLSX, or Parquet format.
- **Member IDs** — find the next available member ID for a given numerical prefix.
- **Certificates** — create individual or bulk membership certificates, list eligible members, and dump all certificates.
- **Transactions** — retrieve paginated transaction logs and filter attendees who paid for preconference and conference.
- **Email campaigns** — create, schedule, send, clone, and report on Zoho Campaigns email campaigns.
- **Mailing lists** — create, subscribe, unsubscribe, and inspect Zoho Campaigns mailing lists and contacts.
- **Notifications** — send zero/partial payment reminders and conference invitations to the correct audience segments.
- **Config management** — interactive environment configuration, masked config display, and disk-cache clearing.

## Requirements

- Python 3.14+
- [uv](https://astral.sh/uv/) (recommended package manager)
- [Ruff](https://docs.astral.sh/ruff/) for linting and formatting

## Installation

```bash
git clone git@github.com:CISON-Official/cli.git
cd cli
uv sync
uv tool install .
```

For a development (editable) install:

```bash
uv tool install --editable .
```

## Configuration

Before running most commands, the CLI must be configured. Setup prompts you for every setting interactively:

```bash
cison configure
```

Configuration is stored in `~/.cison/.env`. To re-create it from scratch:

```bash
cison configure --overwrite
```

Inspect the active configuration at any time (secrets are masked):

```bash
cison config show
```

### Environment variables

| Variable | Description |
| --- | --- |
| `BASE_URL` | Core CISON API base URL (defaults to `https://api.cison.org`) |
| `ADMIN_EMAIL` | Admin email used to authenticate against the API |
| `ADMIN_CERTIFICATE_EXCHANGE_KEY` | RabbitMQ exchange for certificate jobs |
| `ADMIN_CERTIFICATE_ROUTING_KEY` | RabbitMQ routing key for certificate jobs |
| `CELERY_HOST` | Celery/RabbitMQ host |
| `MEMBERSHIP_CERTIFICATION_TASK_NAME` | Name of the membership certification Celery task |
| `EMAIL_API_BASE` | Zoho Campaigns API endpoint |
| `CLIENT_ID` | Zoho OAuth client ID |
| `CLIENT_SECRET` | Zoho OAuth client secret |
| `REFRESH_TOKEN` | Zoho OAuth refresh token |
| `EMAIL_ADMIN` | Sender address used for campaigns |
| `PROGRAM_NAME` | Campaign sender (from) name |
| `CLOUDFLARE_ZONE_ID` | Cloudflare zone for the template host |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token |
| `CLOUDFLARE_MAIN_DOMAIN` | Main domain serving hosted templates |
| `CLOUDFLARE_IP_ADDRESS` | IP used for the template subdomain A record |
| `CLOUDFLARE_SUBDOMAIN` | Subdomain that hosts campaign templates |
| `UPLOAD_ID` | Upload key for publishing templates to the host |
| `MAILINGLIST_LIMIT` | Maximum recipients per mailing list batch |
| `TEST_USEREMAIL_1` … `TEST_USEREMAIL_10` | Test recipient addresses used by notification commands |

## Usage

```bash
cison --help
```

All commands verify configuration before running; only `configure` and `update` are exempt.

### Member management

| Command | Description |
| --- | --- |
| `cison user get-memberid <member_id>` | Get the actual user ID from a member ID |
| `cison user about <user_id>` | Show detailed information about a user |
| `cison user uifmid <member_id>` | Fetch user information directly from a member ID |
| `cison user state` | Categorize users by Nigerian state and export to `data/state/` |
| `cison user search <value>` | Search the user database and export results to CSV + VCF |
| `cison user vmwcp` | Export valid members holding certificates with complete payments |

### Payment data

| Command | Description |
| --- | --- |
| `cison user partial-payments` | Export users with partial payments |
| `cison user no-payments` | Export users without any payments |
| `cison user complete-payments` | Export users with complete payments |

Each accepts `--filename/-f` for the output name and `--format/-fmt` in `csv`, `json`, `xlsx`, or `parquet`.

### Member IDs

| Command | Description |
| --- | --- |
| `cison memberid next-id <prefix>` | Find the first available member ID matching a numeric prefix (e.g. `2`) |
| `cison memberid validate <member_id>` | Validate an existing member ID |

### Certificates

| Command | Description |
| --- | --- |
| `cison certificates membership have-certificate <member_id>` | Check whether a member has a certificate |
| `cison certificates membership create-certificate <member_id>` | Trigger creation of a membership certificate |
| `cison certificates membership get-eligible` | List members currently eligible for a certificate |
| `cison certificates membership bulk-create-certificate <member_ids...>` | Create certificates for many members at once |
| `cison certificates membership all` | Export all certificates to a CSV file |

### Transactions

| Command | Description |
| --- | --- |
| `cison transaction get` | Retrieve transaction logs (options: `--startdate`, `--enddate`, `--per-page`, `--page`) |
| `cison transaction ptppc <pages>` | Export people who paid for both preconference and conference |

### Notifications

| Command | Description |
| --- | --- |
| `cison notification zero-payment` | Send payment reminders to users with no payment |
| `cison notification partial-payment` | Send payment reminders to users with partial payments |
| `cison notification conference` | Send conference reminder campaigns |

### Email campaigns & mailing lists

```
cison emails
├── topic        get-topics | get-products | create
├── campaign     single | list | create | send | schedule | clone |
│                reports | recently-sent | last-report | recipients |
│                coupon-details | coupon-status | delete
└── mailinglist  get | advanced-details | contacts | fields |
                 segment-details | segment-contacts | update | delete |
                 total-contacts | subscribe | unsubscribe | do-not-mail |
                 add-contacts | create | create-field
```

### Maintenance

| Command | Description |
| --- | --- |
| `cison config show` | Display the active configuration with masked secrets |
| `cison config cache-clear` | Clear persistent disk cache (`--force` skips confirmation) |
| `cison update` | Update the CLI to the latest version via `uv` |

## Caching

Frequent API responses (user info, payments, certificates) are cached to disk under `~/.cison/.cache/`. Data is refreshed periodically; clear the cache with:

```bash
cison config cache-clear
```

## Development

```bash
uv sync                      # install dependencies including dev group
uv run ruff check .          # lint
uv run ruff format .         # format
uv build                     # build the wheel into dist/
```

Logs are written chronologically to `logs/<YYYY>/<MM>/<DD>.log`.

## Contributing

See [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md) — create a feature branch, run `ruff`, and open a Pull Request against `main`. Use structured commit messages (`feat:`, `fix:`, `docs:`, `refactor:`).

## Repository

- GitHub: [CISON-Official/cli](https://github.com/CISON-Official/cli)