# Data API Server

Serves items from the data store.

## API Endpoints

- `GET /api/data` -- Returns items from the data store
- `GET /health` -- Health check

## Data Format

The API returns items from the internal data store as a JSON response
with `data` (array of items) and `count` fields.
