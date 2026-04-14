# MeCord AI Service (FastAPI)

Production-like but simple AI microservice for a Discord-like chat app.

The demo prompts, sample data, and smoke tests are all in Vietnamese so you can validate the full flow in the same language as your app.

## 1) Project Structure

```text
ai-service/
  app/
    api/
      routes.py
    clients/
      dynamodb_client.py
      qdrant_client.py
    core/
      config.py
      security.py
    models/
      schemas.py
    services/
      openai_service.py
      search_service.py
    main.py
  examples/
    sample_requests.http
    smoke_test_api.py
    node_fastapi_client.js
  seed/
    create_dynamodb_tables.py
    seed_dynamodb.py
    seed_qdrant.py
  .env.example
  Dockerfile
  requirements.txt
```

## 2) Setup

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Health check: `GET http://localhost:8000/health`

## 2.1) Environment Variables

Minimum variables for local development:

```dotenv
SERVICE_API_KEY=...
OPENAI_API_KEY=...
AWS_REGION=ap-southeast-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
QDRANT_URL=...
QDRANT_API_KEY=...
```

If you run on an AWS host with an IAM role attached, you can omit `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN`.

## 3) API Key Authentication

All `/v1/*` endpoints require header:

```text
X-API-Key: <SERVICE_API_KEY>
```

## 4) Endpoints

### POST /v1/summarize

Input:

```json
{
  "messages": [
    { "role": "user", "content": "We need to finish websocket this week." },
    {
      "role": "assistant",
      "content": "Let's split backend and frontend tasks."
    }
  ]
}
```

Output:

```json
{
  "summary": "- Team plans to complete websocket this week..."
}
```

### POST /v1/chat

Input:

```json
{
  "messages": [
    { "role": "system", "content": "You are a helpful tutor." },
    { "role": "user", "content": "Explain semantic search in simple terms." }
  ]
}
```

Output:

```json
{
  "reply": "Semantic search finds meaning, not only exact words..."
}
```

### POST /v1/embedding

Input:

```json
{
  "text": "How to optimize token usage?"
}
```

Output:

```json
{
  "vector": [0.0123, -0.3321],
  "dimension": 1536
}
```

### POST /v1/search

Flow:

1. Create embedding from query.
2. Search similar vectors in Qdrant.
3. Use payload fields (`group_id`, `message_sk`) to fetch full message from DynamoDB.

Input:

```json
{
  "query": "deadline for project presentation",
  "top_k": 5
}
```

Output:

```json
{
  "results": [
    {
      "score": 0.87,
      "group_id": "f3f5...",
      "message_sk": "MSG#20260413T101010000000Z",
      "message": {
        "PK": "GROUP#f3f5...",
        "SK": "MSG#20260413T101010000000Z",
        "content": "Presentation is next Monday"
      }
    }
  ]
}
```

### POST /v1/speech-to-text

Multipart form-data with `file`.

Output:

```json
{
  "text": "Hello, this is a recorded voice message."
}
```

## 5) DynamoDB Data Model (requested schema)

### Users table

- PK: `USER#<userId>`
- attributes: `username`, `email`, `name`, `created_at`
- GSI: username index

### Groups table

- PK: `GROUP#<groupId>`
- SK: `METADATA` or `USER#<userId>`
- attributes: `name`, `description`, `owner`

### Messages table

- PK: `GROUP#<groupId>`
- SK: `MSG#<timestamp>`
- attributes: `messageId`, `sender`, `content`, `created_at`
- TTL: optional

## 6) Seed Script

Run:

```bash
python seed/create_dynamodb_tables.py
python seed/seed_dynamodb.py
python seed/seed_qdrant.py
```

This creates the DynamoDB tables locally or on AWS, then inserts sample user/group/message records into DynamoDB and searchable embeddings into Qdrant.

## 6.1) Quick Test

Start the API first:

```bash
uvicorn app.main:app --reload
```

Then run the smoke test script:

```bash
python examples/smoke_test_api.py
```

If you want to test speech-to-text, set `SMOKE_TEST_AUDIO_PATH` to a local `.wav` file.

You can also use `examples/sample_requests.http` from VS Code REST Client or Thunder Client.

## 7) Docker

Build and run:

```bash
docker build -t mecord-ai-service .
docker run --env-file .env -p 8000:8000 mecord-ai-service
```

## 8) Node.js Integration Example

See `examples/node_fastapi_client.js`.

Run:

```bash
npm install axios form-data
node examples/node_fastapi_client.js
```

## 9) Cost and Scaling Best Practices

### Cost optimization

- Default to `gpt-4o-mini` for chatbot and summarize.
- Cache summaries by conversation window (for example every 30 messages).
- Do not embed every message in real time if not needed; embed only searchable channels/messages.
- Use shorter context windows: last N messages + compact summary.

### Token usage

- Add strict `max_tokens` per endpoint.
- Keep prompts short and deterministic.
- Use system prompts once and keep them static.
- Trim noisy chat history (emoji spam, repeated bot messages).

### Scaling

- Keep FastAPI stateless; scale replicas horizontally.
- Add background queue for heavy tasks (batch embedding, long transcription).
- Put rate limiting at Node.js gateway level per user/group.
- Add retries with backoff for OpenAI/Qdrant transient failures.

## 10) Suggested 2-4 Week Build Plan

1. Week 1: auth/chat/group APIs + websocket baseline.
2. Week 2: integrate AI `/chat` and `/summarize`.
3. Week 3: embeddings + Qdrant semantic search.
4. Week 4: speech-to-text + polish + load test + demo script.
