# Hello-github

A simple Node.js API built with Express.

## Available routes

- `GET /` - API root with route metadata
- `GET /health` - returns service health status
- `POST /echo` - echoes back the JSON payload sent in the request body

## Run locally

1. Install dependencies:

```bash
npm install
```

2. Start the server:

```bash
npm start
```

3. Open http://localhost:3000 in your browser or use curl:

```bash
curl http://localhost:3000
```

## Example echo request

```bash
curl -X POST http://localhost:3000/echo \
  -H "Content-Type: application/json" \
  -d '{"name":"GitHub","message":"Hello"}'
```
