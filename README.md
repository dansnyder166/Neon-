# neon_test

A Python websocket-powered AI co-pilot agent for the Neon challenge.



## Requirements

- Python 3.12+
- `uv` CLI (Neon interpreter)

## Ensure `uv` is installed

Before continuing, make sure `uv` is installed and on your PATH. On Debian/Ubuntu:

```bash
sudo apt update
sudo apt install uv
```

On other platforms, follow Neon docs for `uv` installation.

## Setup

1. Create and activate virtual environment (recommended):

```bash
uv sync
source .venv/bin/activate
```

2. Install dependencies via `uv sync` (or pip if `uv` doesn't resolve):

```bash
uv sync
# or
pip install -r requirements.txt
```

3. Set environment variables in `.env` in project root:

```ini
MODEL=gemini-3-flash-preview
GOOGLE_API_KEY="***"
SATELLITE_URI=wss://neonhealth.software/agent-puzzle/challenge
NEON_CODE="***"
```

4. Confirm `.env` is loaded and accessible:

```bash
python -c "from dotenv import load_dotenv, os; load_dotenv(); print(os.getenv('NEON_CODE'))"
```

## Usage

Run the application:

```bash
uv run main.py
```

For local debug (direct Python):

```bash
python3 main.py
```

## Docker

Build the image:

```bash
docker build -t neon_test:latest .
```

Run the container (mount env file):

```bash
docker run --rm \
  --env-file .env \
  neon_test:latest
```

If you need to pass the websocket URL or keys at runtime:

```bash
docker run --rm \
  -e MODEL=gemini-3-flash-preview \
  -e GOOGLE_API_KEY=your_api_key \
  -e SATELLITE_URI=wss://neonhealth.software/agent-puzzle/challenge \
  -e NEON_CODE=****** \
  neon_test:latest
```


## Notes

- The code handles retries and websocket timeouts.
- `SYSTEM_PROMPT` is injected at startup and the agent keeps recent conversation history.
- Use `uv` for project-managed environment and dependency resolution.
