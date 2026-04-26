# CLI examples

The `llm-safe` console script wraps the same functionality as the Python API, useful for shell pipelines and quick one-off checks.

## Install

```bash
pip install llm-safe-pl
```

## Detect

Find PII without modifying the file. JSON output is the default (pipeline-friendly); `--format text` emits tab-separated rows.

```bash
llm-safe detect document.txt
# [
#   { "type": "pesel", "value": "44051401359", "start": 15, "end": 26, "detector": "pesel" },
#   { "type": "email", "value": "jan@example.pl", "start": 38, "end": 52, "detector": "email" }
# ]

llm-safe detect document.txt --format text
# pesel   15-26   44051401359
# email   38-52   jan@example.pl
```

Pipe into `jq` or `awk` for scripting:

```bash
llm-safe detect document.txt | jq '.[] | .type' | sort -u
llm-safe detect document.txt --format text | awk -F'\t' '{print $1}' | sort -u
```

## Anonymize

Writes two files: the anonymized text and a JSON mapping that lets you restore the originals later.

```bash
llm-safe anonymize document.txt -o anonymized.txt -m mapping.json
cat anonymized.txt
# "Klient [PESEL_001] zamówił dostawę, kontakt: [EMAIL_001]."

cat mapping.json
# {"schema_version": 1, "counters": {...}, "entries": [{"token": "[PESEL_001]", ...}]}
```

Now it's safe to send `anonymized.txt` to any LLM API.

Re-running on the same outputs requires `--force` (since v0.2.0). The CLI refuses to silently overwrite an existing `-o` or `-m` file:

```bash
llm-safe anonymize document.txt -o anonymized.txt -m mapping.json
# Usage: llm-safe anonymize ...
# Error: anonymized.txt exists; pass --force to overwrite

llm-safe anonymize document.txt -o anonymized.txt -m mapping.json --force
# (overwrites both)
```

## Deanonymize

Restore original values using a mapping produced by `anonymize`.

```bash
# To stdout (omit --output)
llm-safe deanonymize anonymized.txt -m mapping.json

# To a file
llm-safe deanonymize anonymized.txt -m mapping.json -o restored.txt

# --force is required to overwrite an existing output file (since v0.2.0)
llm-safe deanonymize anonymized.txt -m mapping.json -o restored.txt --force
```

## End-to-end round-trip in one shell

```bash
# 1) Anonymize.
llm-safe anonymize input.txt -o anon.txt -m map.json

# 2) Call an LLM (pseudocode — substitute your actual HTTP client).
curl -sS https://api.example.com/llm \
    -H "Authorization: Bearer $API_KEY" \
    -d @anon.txt > llm_response.txt

# 3) Deanonymize the response.
llm-safe deanonymize llm_response.txt -m map.json -o final.txt
```

## Stdin / stdout pipelines

Every subcommand accepts `-` as the input path, meaning "read from stdin". `deanonymize --output -` additionally means "write to stdout" (equivalent to omitting `--output`).

```bash
# Anonymize from stdin, text and mapping still go to files.
echo "PESEL 44051401359" | llm-safe anonymize - -o anon.txt -m map.json

# Deanonymize from stdin; restored text goes to stdout.
cat anon.txt | llm-safe deanonymize - -m map.json

# Detect on stdin.
echo "PESEL 44051401359" | llm-safe detect -
```

Note: `--mapping` is always a file path. Piping structural state between commands is more footgun than feature.

## File encodings

The CLI accepts UTF-8 (with or without BOM) and UTF-16 LE/BE when a BOM is present. On Windows PowerShell 5.1, `echo "..." > file.txt` produces UTF-16 LE with BOM by default — that just works.

Output is always canonical UTF-8 without BOM.

## Input-size cap

Every subcommand supports `--max-bytes` (default 64 MiB). Inputs larger than that are refused with a clear error instead of being slurped into memory. Useful when piping from an untrusted source:

```bash
# Refuse anything over 1 MiB.
some_user_program | llm-safe anonymize - -o out.txt -m map.json --max-bytes $((1024 * 1024))
```

Set it lower than the default if you know your real inputs are bounded; raising it above 64 MiB is allowed but treats the host's RAM as the only ceiling.

## Help

```bash
llm-safe --help
llm-safe anonymize --help
llm-safe deanonymize --help
llm-safe detect --help
```
