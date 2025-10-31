# Configuration Schema

Jellyfleet uses a YAML configuration file with the following structure:

## Servers

```yaml
servers:
  server-id:
    url: https://example
    token:
      value: secret-token
```

Tokens may reference environment variables or files:

```yaml
token:
  env: JELLYFLEET_TOKEN
```

Or reference a file containing the token:

```yaml
token:
  file: /path/to/token.txt
```

## Combinations

```yaml
combinations:
  - name: sync-run
    father: server-id
    children:
      - server: child-id
        domains: [users, libraries, settings]
```

## Scheduler

```yaml
scheduler:
  cron: "0 */6 * * *"
  timezone: UTC
```

## Runtime

```yaml
runtime:
  dry_run: false
```

## Environment Variables

Jellyfleet supports environment variable overrides for configuration:

- `JELLYFLEET_DB_PATH`: Override database path
- `JELLYFLEET_LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `JELLYFLEET_DRY_RUN`: Override dry run setting (true/false)
- `JELLYFLEET_SECRETS_DIR`: Directory for secret files

## Configuration Validation

Use the CLI to validate your configuration:

```bash
jellyfleet --config config.yaml validate
```

## Secret Management

For better security, use environment variables or secret files instead of plain text tokens:

```yaml
servers:
  production:
    url: https://jellyfin.example.com
    token:
      env: JELLYFIN_PROD_TOKEN
```

Create a secrets directory and reference files:

```bash
mkdir secrets
echo "your-secret-token" > secrets/jellyfin-token.txt
```

```yaml
servers:
  production:
    url: https://jellyfin.example.com
    token:
      file: secrets/jellyfin-token.txt
```
