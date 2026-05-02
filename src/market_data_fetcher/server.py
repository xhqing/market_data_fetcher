import json
import logging

from mcp.server.fastmcp import FastMCP

from market_data_fetcher.config import (
    get_indices_from_config,
    get_stocks_from_config,
    get_etfs_from_config,
    load_targets_config,
)
from market_data_fetcher import longport_client
from market_data_fetcher import akshare_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "market-data-fetcher",
    instructions="Market data fetching MCP Server. Supports Longport API and AKShare as data sources for Hong Kong and US stock market data including indices, stocks, and ETFs.",
)


@mcp.tool()
def fetch_index_data(source: str = "longport") -> str:
    """Fetch latest index data for Hong Kong and US markets.

    Args:
        source: Data source - "longport" (Longport API, requires credentials),
                "akshare" (AKShare/Sina Finance, free), or "both" (try Longport first, fallback to AKShare).
                Default is "longport".

    Returns:
        JSON string containing index data with fields: name, code, price, timestamp, source.
    """
    config = load_targets_config()
    indices = get_indices_from_config(config)

    if not indices:
        return json.dumps({"error": "No indices configured in targets.json"}, ensure_ascii=False)

    results = []

    if source == "akshare":
        results = akshare_client.fetch_all_index_data()
    elif source == "longport":
        if not longport_client.is_available():
            return json.dumps({"error": "Longport SDK not available. Install with: pip install longport", "suggestion": "Use source='akshare' as fallback"}, ensure_ascii=False)
        results = longport_client.fetch_index_data(indices)
    elif source == "both":
        results = longport_client.fetch_index_data(indices)
        failed = [r for r in results if r.get("price") is None]
        if failed and longport_client.is_available():
            failed_names = {r["name"] for r in failed}
            ak_results = akshare_client.fetch_all_index_data()
            for ar in ak_results:
                if ar["name"] in failed_names and ar.get("price") is not None:
                    for i, r in enumerate(results):
                        if r["name"] == ar["name"]:
                            results[i] = ar
                            break
    else:
        return json.dumps({"error": f"Unknown source: {source}. Use 'longport', 'akshare', or 'both'."}, ensure_ascii=False)

    return json.dumps({"data": results, "count": len(results)}, ensure_ascii=False, default=str)


@mcp.tool()
def fetch_stock_data(codes: list[str] | None = None, source: str = "longport") -> str:
    """Fetch latest stock data for Hong Kong stocks.

    Args:
        codes: Optional list of stock codes to fetch (e.g., ["00700.HK", "09988.HK"]).
               If not provided, fetches all stocks from targets.json.
        source: Data source - "longport" or "akshare". Default is "longport".

    Returns:
        JSON string containing stock data with fields: name, code, price, timestamp, source.
    """
    config = load_targets_config()
    all_stocks = get_stocks_from_config(config)

    if codes:
        stocks = [s for s in all_stocks if s["code"] in codes]
        if not stocks:
            return json.dumps({"error": f"No matching stocks found for codes: {codes}"}, ensure_ascii=False)
    else:
        stocks = all_stocks

    if not stocks:
        return json.dumps({"error": "No stocks configured in targets.json"}, ensure_ascii=False)

    results = []

    if source == "akshare":
        results = akshare_client.fetch_hk_stock_data(stocks)
    elif source == "longport":
        if not longport_client.is_available():
            return json.dumps({"error": "Longport SDK not available", "suggestion": "Use source='akshare' as fallback"}, ensure_ascii=False)
        results = longport_client.fetch_stock_list_data(stocks)
    else:
        return json.dumps({"error": f"Unknown source: {source}"}, ensure_ascii=False)

    return json.dumps({"data": results, "count": len(results)}, ensure_ascii=False, default=str)


@mcp.tool()
def fetch_etf_data(codes: list[str] | None = None, source: str = "longport") -> str:
    """Fetch latest ETF data for Hong Kong and US ETFs.

    Args:
        codes: Optional list of ETF codes to fetch (e.g., ["02800.HK", "03033.HK"]).
               If not provided, fetches all ETFs from targets.json.
        source: Data source - "longport" or "akshare". Default is "longport".

    Returns:
        JSON string containing ETF data with fields: name, code, price, timestamp, source.
    """
    config = load_targets_config()
    all_etfs = get_etfs_from_config(config)

    if codes:
        etfs = [e for e in all_etfs if e["code"] in codes]
        if not etfs:
            return json.dumps({"error": f"No matching ETFs found for codes: {codes}"}, ensure_ascii=False)
    else:
        etfs = all_etfs

    if not etfs:
        return json.dumps({"error": "No ETFs configured in targets.json"}, ensure_ascii=False)

    results = []

    if source == "akshare":
        hk_etfs = [e for e in etfs if e["code"].endswith(".HK")]
        results = akshare_client.fetch_hk_etf_data(hk_etfs)
    elif source == "longport":
        if not longport_client.is_available():
            return json.dumps({"error": "Longport SDK not available", "suggestion": "Use source='akshare' as fallback"}, ensure_ascii=False)
        results = longport_client.fetch_etf_list_data(etfs)
    else:
        return json.dumps({"error": f"Unknown source: {source}"}, ensure_ascii=False)

    return json.dumps({"data": results, "count": len(results)}, ensure_ascii=False, default=str)


@mcp.tool()
def fetch_all_market_data(source: str = "longport") -> str:
    """Fetch all market data at once: indices, stocks, and ETFs.

    Args:
        source: Data source - "longport", "akshare", or "both". Default is "longport".

    Returns:
        JSON string containing all market data grouped by type.
    """
    index_result = json.loads(fetch_index_data(source=source))
    stock_result = json.loads(fetch_stock_data(source=source))
    etf_result = json.loads(fetch_etf_data(source=source))

    return json.dumps({
        "index_data": index_result,
        "stock_data": stock_result,
        "etf_data": etf_result,
    }, ensure_ascii=False, default=str)


@mcp.tool()
def get_targets_config() -> str:
    """Read and return the current targets.json configuration.

    Returns:
        JSON string of the targets.json content.
    """
    config = load_targets_config()
    return json.dumps(config, ensure_ascii=False, indent=2)


@mcp.tool()
def check_longport_status() -> str:
    """Check if Longport SDK is available and credentials are configured.

    Returns:
        JSON string with availability status and credential check results.
    """
    from market_data_fetcher.config import get_longport_credentials

    available = longport_client.is_available()
    creds = get_longport_credentials()
    has_key = bool(creds["app_key"])
    has_secret = bool(creds["app_secret"])
    has_token = bool(creds["access_token"])

    return json.dumps({
        "sdk_installed": available,
        "credentials": {
            "app_key": "configured" if has_key else "missing",
            "app_secret": "configured" if has_secret else "missing",
            "access_token": "configured" if has_token else "missing",
        },
        "ready": available and has_key and has_secret and has_token,
    }, ensure_ascii=False)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
