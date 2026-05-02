# market-data-fetcher

MCP Server for fetching market data from Longport API and AKShare.

## Features

- Fetch Hong Kong and US index data
- Fetch Hong Kong stock data
- Fetch Hong Kong and US ETF data
- Support multiple data sources: Longport API, AKShare (Sina Finance)
- Automatic fallback from Longport to AKShare

## Installation

```bash
pip install market-data-fetcher
```

### With Longport SDK

```bash
pip install "market-data-fetcher[longport]"
```

## Usage

### As MCP Server

```bash
market-data-fetcher
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LONGPORT_APP_KEY` | Longport API App Key | For Longport source |
| `LONGPORT_APP_SECRET` | Longport API App Secret | For Longport source |
| `LONGPORT_ACCESS_TOKEN` | Longport API Access Token | For Longport source |
| `TARGETS_JSON_PATH` | Path to targets.json | Optional (defaults to project root) |

## MCP Tools

| Tool | Description |
|------|-------------|
| `fetch_index_data` | Fetch index data for HK and US markets |
| `fetch_stock_data` | Fetch stock data for HK stocks |
| `fetch_etf_data` | Fetch ETF data for HK and US ETFs |
| `fetch_all_market_data` | Fetch all market data at once |
| `get_targets_config` | Read targets.json configuration |
| `check_longport_status` | Check Longport SDK and credentials status |

## License

AGPL-3.0
