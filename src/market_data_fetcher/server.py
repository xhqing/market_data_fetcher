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
from market_data_fetcher import yfinance_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "market-data-fetcher",
    instructions="Market data fetching MCP Server. Supports Longport API, AKShare, and Yahoo Finance (yfinance) as data sources for Hong Kong and US stock market data including indices, stocks, and ETFs.",
)

VALID_SOURCES = ("longport", "akshare", "yfinance", "both")


def _fallback_results(results, fallback_data, source_name="fallback"):
    failed = [r for r in results if r.get("price") is None]
    if not failed:
        return results
    failed_names = {r["name"] for r in failed}
    for fr in fallback_data:
        if fr["name"] in failed_names and fr.get("price") is not None:
            for i, r in enumerate(results):
                if r["name"] == fr["name"]:
                    fr_copy = dict(fr)
                    fr_copy["source"] = fr.get("source", source_name) + f" (fallback from {results[i].get('source', 'unknown')})"
                    results[i] = fr_copy
                    break
    return results


@mcp.tool()
def fetch_index_data(source: str = "longport") -> str:
    """Fetch latest index data for Hong Kong and US markets.

    Args:
        source: Data source - "longport" (Longport API, requires credentials),
                "akshare" (AKShare/Sina Finance, free), "yfinance" (Yahoo Finance, free),
                or "both" (try Longport first, fallback to yfinance then akshare).
                Default is "longport".

    Returns:
        JSON string containing index data with fields: name, code, price, timestamp, source.
    """
    config = load_targets_config()
    indices = get_indices_from_config(config)

    if not indices:
        return json.dumps({"error": "No indices configured in targets.json"}, ensure_ascii=False)

    if source not in VALID_SOURCES:
        return json.dumps({"error": f"Unknown source: {source}. Use {VALID_SOURCES}."}, ensure_ascii=False)

    results = []

    if source == "akshare":
        results = akshare_client.fetch_all_index_data()
    elif source == "yfinance":
        if not yfinance_client.is_available():
            return json.dumps({"error": "yfinance not available. Install with: pip install yfinance", "suggestion": "Use source='akshare' as fallback"}, ensure_ascii=False)
        results = yfinance_client.fetch_all_index_data(indices)
    elif source == "longport":
        if not longport_client.is_available():
            return json.dumps({"error": "Longport SDK not available. Install with: pip install longport", "suggestion": "Use source='yfinance' or 'akshare' as fallback"}, ensure_ascii=False)
        results = longport_client.fetch_index_data(indices)
    elif source == "both":
        if longport_client.is_available():
            results = longport_client.fetch_index_data(indices)
        else:
            results = [{"name": idx["name"], "code": idx["code"], "price": None, "timestamp": None, "source": "Longport API (unavailable)"} for idx in indices]

        failed = [r for r in results if r.get("price") is None]
        if failed:
            if yfinance_client.is_available():
                yf_results = yfinance_client.fetch_all_index_data(indices)
                results = _fallback_results(results, yf_results, "Yahoo Finance")

            still_failed = [r for r in results if r.get("price") is None]
            if still_failed:
                ak_results = akshare_client.fetch_all_index_data()
                results = _fallback_results(results, ak_results, "AKShare")

    return json.dumps({"data": results, "count": len(results)}, ensure_ascii=False, default=str)


@mcp.tool()
def fetch_stock_data(codes: list[str] | None = None, source: str = "longport") -> str:
    """Fetch latest stock data for Hong Kong and US stocks.

    Args:
        codes: Optional list of stock codes to fetch (e.g., ["00700.HK", "09988.HK"]).
               If not provided, fetches all stocks from targets.json.
        source: Data source - "longport", "akshare", "yfinance", or "both". Default is "longport".

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

    if source not in VALID_SOURCES:
        return json.dumps({"error": f"Unknown source: {source}. Use {VALID_SOURCES}."}, ensure_ascii=False)

    results = []

    if source == "akshare":
        results = akshare_client.fetch_hk_stock_data(stocks)
    elif source == "yfinance":
        if not yfinance_client.is_available():
            return json.dumps({"error": "yfinance not available", "suggestion": "Use source='akshare' as fallback"}, ensure_ascii=False)
        hk_stocks = [s for s in stocks if s["code"].endswith(".HK")]
        us_stocks = [s for s in stocks if not s["code"].endswith(".HK")]
        results = []
        if hk_stocks:
            results.extend(yfinance_client.fetch_hk_stock_data(hk_stocks))
        if us_stocks:
            results.extend(yfinance_client.fetch_us_stock_data(us_stocks))
    elif source == "longport":
        if not longport_client.is_available():
            return json.dumps({"error": "Longport SDK not available", "suggestion": "Use source='yfinance' or 'akshare' as fallback"}, ensure_ascii=False)
        results = longport_client.fetch_stock_list_data(stocks)
    elif source == "both":
        if longport_client.is_available():
            results = longport_client.fetch_stock_list_data(stocks)
        else:
            results = [{"name": s["name"], "code": s["code"], "price": None, "timestamp": None, "source": "Longport API (unavailable)"} for s in stocks]

        failed = [r for r in results if r.get("price") is None]
        if failed:
            if yfinance_client.is_available():
                hk_stocks = [s for s in stocks if s["code"].endswith(".HK")]
                us_stocks = [s for s in stocks if not s["code"].endswith(".HK")]
                yf_results = []
                if hk_stocks:
                    yf_results.extend(yfinance_client.fetch_hk_stock_data(hk_stocks))
                if us_stocks:
                    yf_results.extend(yfinance_client.fetch_us_stock_data(us_stocks))
                results = _fallback_results(results, yf_results, "Yahoo Finance")

            still_failed = [r for r in results if r.get("price") is None]
            if still_failed:
                ak_results = akshare_client.fetch_hk_stock_data(stocks)
                results = _fallback_results(results, ak_results, "AKShare")

    return json.dumps({"data": results, "count": len(results)}, ensure_ascii=False, default=str)


@mcp.tool()
def fetch_etf_data(codes: list[str] | None = None, source: str = "longport") -> str:
    """Fetch latest ETF data for Hong Kong and US ETFs.

    Args:
        codes: Optional list of ETF codes to fetch (e.g., ["02800.HK", "03033.HK"]).
               If not provided, fetches all ETFs from targets.json.
        source: Data source - "longport", "akshare", "yfinance", or "both". Default is "longport".

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

    if source not in VALID_SOURCES:
        return json.dumps({"error": f"Unknown source: {source}. Use {VALID_SOURCES}."}, ensure_ascii=False)

    results = []

    if source == "akshare":
        hk_etfs = [e for e in etfs if e["code"].endswith(".HK")]
        us_etfs = [e for e in etfs if not e["code"].endswith(".HK")]
        results = akshare_client.fetch_hk_etf_data(hk_etfs)
        if us_etfs and yfinance_client.is_available():
            results.extend(yfinance_client.fetch_us_etf_data(us_etfs))
        elif us_etfs:
            for etf in us_etfs:
                results.append({"name": etf["name"], "code": etf["code"], "price": None, "timestamp": None, "source": "", "error": "US ETF data requires yfinance or longport"})
    elif source == "yfinance":
        if not yfinance_client.is_available():
            return json.dumps({"error": "yfinance not available", "suggestion": "Use source='akshare' for HK ETFs only"}, ensure_ascii=False)
        hk_etfs = [e for e in etfs if e["code"].endswith(".HK")]
        us_etfs = [e for e in etfs if not e["code"].endswith(".HK")]
        results = []
        if hk_etfs:
            results.extend(yfinance_client.fetch_hk_etf_data(hk_etfs))
        if us_etfs:
            results.extend(yfinance_client.fetch_us_etf_data(us_etfs))
    elif source == "longport":
        if not longport_client.is_available():
            return json.dumps({"error": "Longport SDK not available", "suggestion": "Use source='yfinance' or 'akshare' as fallback"}, ensure_ascii=False)
        results = longport_client.fetch_etf_list_data(etfs)
    elif source == "both":
        if longport_client.is_available():
            results = longport_client.fetch_etf_list_data(etfs)
        else:
            results = [{"name": e["name"], "code": e["code"], "price": None, "timestamp": None, "source": "Longport API (unavailable)"} for e in etfs]

        failed = [r for r in results if r.get("price") is None]
        if failed:
            if yfinance_client.is_available():
                hk_etfs = [e for e in etfs if e["code"].endswith(".HK")]
                us_etfs = [e for e in etfs if not e["code"].endswith(".HK")]
                yf_results = []
                if hk_etfs:
                    yf_results.extend(yfinance_client.fetch_hk_etf_data(hk_etfs))
                if us_etfs:
                    yf_results.extend(yfinance_client.fetch_us_etf_data(us_etfs))
                results = _fallback_results(results, yf_results, "Yahoo Finance")

            still_failed = [r for r in results if r.get("price") is None]
            if still_failed:
                hk_etfs = [e for e in etfs if e["code"].endswith(".HK")]
                ak_results = akshare_client.fetch_hk_etf_data(hk_etfs)
                results = _fallback_results(results, ak_results, "AKShare")

    return json.dumps({"data": results, "count": len(results)}, ensure_ascii=False, default=str)


@mcp.tool()
def fetch_all_market_data(source: str = "longport") -> str:
    """Fetch all market data at once: indices, stocks, and ETFs.

    Args:
        source: Data source - "longport", "akshare", "yfinance", or "both". Default is "longport".

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
