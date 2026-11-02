---
name: fosun-env-setup
description: Creates and repairs the shared OpenAPI credential file fosun.env. Covers first signup, a new device, a lost credential, an expired API key, and an invalid credential. A backfill of an existing account must include both the API key and the server public key from the page. fosun.env is written only after verification.
requires:
  bins:
    - python3
---

# fosun-env-setup

Language: chat replies follow the user's language. Do not print key material.

This module only creates and repairs the shared `fosun.env`. It does not place paper or live orders.

`serverPubKey` is minted per ticket and changes every time. The client private key, the server public key, and the authorization URL are one ticket. Do not mix tickets. If backfill is rejected, reuse the current QR code and do not rotate keys.

## Credential model

- One account, one OpenAPI API key.
- One API key, one client key pair plus the server key. The file stores the API key, the client private key, and the server public key.

## Three cases

| Case | When | Command | URL | Rotate client key | User sends back |
|------|------|---------|-----|-------------------|-----------------|
| 1 First time, new device, or lost file | No usable credential. Default entry | `ensure_fosun_env.py` | Normal signup page | Generate only if missing | After Forgot API parameters: **API key + server public key** |
| 2 Expired renewal | Business code 40010, or an explicit renewal | `ensure_fosun_env.py --renew` | Hash includes `isExpired=1` | No | No |
| 3 Invalid or damaged | Business code 40001/40015, or an explicit reset | `ensure_fosun_env.py --reset-credentials` | Normal signup page | **Yes** | **Yes: API key + server public key** |

Case 1 cannot tell a new device from a lost file. `user_message` / `operation_guide` say so. If they have signed up before, they tap **Forgot API parameters**, then send the **API key and the server public key (PEM)** together. Run `--api-key` and `--server-public-key`. The pending client private key for this ticket is promoted into `fosun.env`, then verified.

> An existing account must send **API key + server public key** together. Do not write the API key alone. The page public key is not the ticket's temporary public key. A first-time signup only needs them to say it is ready. Renewal needs no paste.

> A new device has no local API key, so `--renew` cannot run first. Order: 1) default entry and QR code; 2) they tap Forgot API parameters and send **API key + server public key**; 3) write both; 4) finalize sees expiry and switches to renewal.

## Paths

- Default: the setup script own path under the home directory, outside the skill, shared with `moni-trade-skill` and `real-trade-skill`.
- `FOSUN_ENV_PATH` overrides it.
- A relative `FOSUN_ENV_PATH` resolves under the default credential directory, not the shell cwd.
- A verified file is also backed up outside the skill: macOS `~/Library/Application Support/fw-trade-skill/fosun-env-backups`, Linux `${XDG_DATA_HOME:-~/.local/share}/fw-trade-skill/fosun-env-backups`, Windows `%LOCALAPPDATA%\fw-trade-skill\fosun-env-backups`.
- `FOSUN_ENV_BACKUP_DIR` overrides the backup directory. A relative path resolves from the home directory.

## Case 1

```bash
python3 fosun-env-setup/code/ensure_fosun_env.py
```

Immediately calls TicketCreate for a new ticket (`credential_scenario=setup`, `created_new_ticket=true`). It does not reuse a cached ticket. If they already finished on the page, the script tries finalize first. `status=valid` is success. Failure mints a new ticket.

Send `exact_open_url` in the reply and `deliver_attachments` with `qr_png_path`. Ask whether they can see the image. If not, ask what they see and try another way. Do not use Read to show the image. Do not send only the link.

## Case 2

```bash
python3 fosun-env-setup/code/ensure_fosun_env.py --renew
```

`real-trade-skill` uses the same path on `40010`. The URL hash includes `isExpired=1`. The API key and the client private key stay. After they scan, retry the original action.

Renewal needs a local API key and server public key. A new device cannot renew directly. Follow the new-device order above.

## Backfill

Use this when they tapped Forgot API parameters, after a case-3 reset, or on a new device. A first-time signup does not use this command. They say it is ready, then you rerun the default entry.

Both are required:

1. **API key:** the `ak_...` value copied from the authorization page.
2. **Server public key:** the `-----BEGIN PUBLIC KEY-----` … `-----END PUBLIC KEY-----` block on that same page.

Do not run `--api-key` without `--server-public-key`. Use the key from the page, not the temporary `serverPubKey` from TicketCreate. The client private key is promoted from this ticket. They do not send it.

```bash
python3 fosun-env-setup/code/ensure_fosun_env.py \
  --api-key '<API key from the page>' \
  --server-public-key '<server public key PEM from the page>'
```

After `install.sh`, `$FOSUN_PY` may replace `python3`. If they send only the API key, ask for the server public key from the same page, then run the command once.

## Case 3

```bash
python3 fosun-env-setup/code/ensure_fosun_env.py --reset-credentials
```

Also used on `40001` / `40015`. The script rotates the client key pair and calls TicketCreate. They tap **Forgot API parameters**, then follow Backfill.

> If backfill returns `api_key_rejected=true` and `created_new_ticket=false`, reuse the current QR code. They tap Forgot API parameters again on that same page and send a fresh API key plus server public key. Run the full backfill again. Do not mint a new ticket and do not rotate keys.

## Results

- `status=pending`: a new signup, renewal, or reset URL (`created_new_ticket=true`). Read `credential_scenario` and `operation_guide`. Send `qr_media.path` and `exact_open_url`. Pending material stays in pending state. `fosun.env` does not store `pending` credentials.
- `status=valid`: the shared credential is usable.
- `status=error`: local dependency, network, or auth failed. Stop.

If `fosun.env` is missing or incomplete, the script restores a user-level backup and checks it again. Success includes `restored_from_backup`.

## Deleted file

Run `ensure_fosun_env.py` or `--repair`. Do not copy a backup by hand, do not ask them for the client private key, and do not try to recover `FSOPENAPI_CLIENT_PRIVATE_KEY` from the server. It is generated only on this machine.

`status=valid` with `restored_from_backup` means it was restored. No new scan. If the backup is gone too, use case 1. If the API key is still rejected, use case 3 and then Backfill.

## Other flags

```bash
python3 fosun-env-setup/code/ensure_fosun_env.py --repair
python3 fosun-env-setup/code/ensure_fosun_env.py --force-new-ticket
```

## Output

The script prints JSON only. Never show `fosun.env` secrets. On `status=pending`, report `credential_scenario`, `user_message`, `operation_guide`, `qr_media`, `exact_open_url`, and `next_action` in English. When backfill is required, wait for both the API key and the server public key, then run both flags. Do not write the API key alone.
