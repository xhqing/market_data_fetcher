import logging
import os
import time
from datetime import datetime, timezone

import pytz

logger = logging.getLogger(__name__)

YFINANCE_AVAILABLE = False
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
    logger.info("yfinance library available")
except ImportError:
    logger.warning("yfinance not installed, install with: pip install yfinance")

_PROXY_URL = os.environ.get("YFINANCE_PROXY", "")


def _get_session():
    if not _PROXY_URL:
        return None
    try:
        import requests
        session = requests.Session()
        session.proxies = {"http": _PROXY_URL, "https": _PROXY_URL}
        logger.info(f"yfinance using proxy: {_PROXY_URL}")
        return session
    except Exception as e:
        logger.warning(f"Failed to set yfinance proxy: {e}")
        return None

us_eastern_tz = pytz.timezone("US/Eastern")
bj_tz = pytz.timezone("Asia/Shanghai")

US_INDEX_YF_MAP = {
    "纳斯达克100指数": "^NDX",
    "标普500指数": "^GSPC",
    "道琼斯工业指数": "^DJI",
    "道琼斯指数": "^DJI",
}

HK_INDEX_YF_MAP = {
    "恒生指数": "^HSI",
    "恒生科技指数": "^HSTECH",
    "国企指数": "^HSCE",
}


def is_available():
    return YFINANCE_AVAILABLE


def _hk_code_to_yf(code):
    if code.endswith(".HK"):
        stripped = code.replace(".HK", "")
        stripped = stripped.lstrip("0")
        if stripped.isdigit():
            return stripped.zfill(4) + ".HK"
        return code
    return code


def _us_index_to_yf_symbol(name, code):
    if name in US_INDEX_YF_MAP:
        return US_INDEX_YF_MAP[name]
    if code.startswith("^"):
        return code
    if code == ".NDX":
        return "^NDX"
    if code == ".SPX":
        return "^GSPC"
    if code == ".DJI":
        return "^DJI"
    return code


def _format_us_timestamp(dt):
    if dt is None:
        return None
    try:
        if dt.tzinfo is None:
            dt = us_eastern_tz.localize(dt)
        else:
            dt = dt.astimezone(us_eastern_tz)
        return dt.strftime("%Y-%m-%d %H:%M:%S") + " (美东时间)"
    except Exception:
        return str(dt)


def _format_hk_timestamp(dt):
    if dt is None:
        return None
    try:
        if dt.tzinfo is None:
            dt = bj_tz.localize(dt)
        else:
            dt = dt.astimezone(bj_tz)
        return dt.strftime("%Y-%m-%d %H:%M:%S") + " (北京时间)"
    except Exception:
        return str(dt)


def _fetch_yf_data(symbol, is_us=True):
    try:
        ticker = yf.Ticker(symbol, session=_get_session())
        hist = ticker.history(period="1d")
        if hist is not None and not hist.empty:
            latest = hist.iloc[-1]
            price = round(float(latest["Close"]), 2)
            ts = latest.name
            return price, ts
        return None, None
    except Exception as e:
        logger.warning(f"yfinance: failed to fetch {symbol}: {e}")
        return None, None


def fetch_us_index_data(indices):
    results = []
    for idx in indices:
        yf_symbol = _us_index_to_yf_symbol(idx["name"], idx["code"])
        price, ts = _fetch_yf_data(yf_symbol, is_us=True)
        time_str = _format_us_timestamp(ts) if ts else None
        source = "https://finance.yahoo.com/quote/" + yf_symbol.replace("^", "%5E")
        results.append({
            "name": idx["name"],
            "code": idx["code"],
            "price": price,
            "timestamp": time_str,
            "source": source,
        })
        logger.info(f"yfinance: {idx['name']} ({yf_symbol}): {price}")
        time.sleep(0.3)
    return results


def fetch_hk_index_data(indices):
    results = []
    for idx in indices:
        yf_symbol = HK_INDEX_YF_MAP.get(idx["name"], _hk_code_to_yf(idx["code"]))
        price, ts = _fetch_yf_data(yf_symbol, is_us=False)
        time_str = _format_hk_timestamp(ts) if ts else None
        source = "https://finance.yahoo.com/quote/" + yf_symbol.replace("^", "%5E")
        results.append({
            "name": idx["name"],
            "code": idx["code"],
            "price": price,
            "timestamp": time_str,
            "source": source,
        })
        logger.info(f"yfinance: {idx['name']} ({yf_symbol}): {price}")
        time.sleep(0.3)
    return results


def fetch_all_index_data(indices):
    hk_indices = [idx for idx in indices if idx["name"] in HK_INDEX_YF_MAP or idx["code"].endswith(".HK") or idx["code"] in ("HSI", "HSTECH", "HSCEI")]
    us_indices = [idx for idx in indices if idx not in hk_indices]
    results = []
    if hk_indices:
        results.extend(fetch_hk_index_data(hk_indices))
    if us_indices:
        results.extend(fetch_us_index_data(us_indices))
    return results


def fetch_us_stock_data(stocks):
    results = []
    for stock in stocks:
        symbol = stock["code"]
        price, ts = _fetch_yf_data(symbol, is_us=True)
        time_str = _format_us_timestamp(ts) if ts else None
        source = "https://finance.yahoo.com/quote/" + symbol
        results.append({
            "name": stock["name"],
            "code": stock["code"],
            "price": price,
            "timestamp": time_str,
            "source": source,
        })
        logger.info(f"yfinance: {stock['name']} ({symbol}): {price}")
        time.sleep(0.3)
    return results


def fetch_hk_stock_data(stocks):
    results = []
    for stock in stocks:
        yf_symbol = _hk_code_to_yf(stock["code"])
        price, ts = _fetch_yf_data(yf_symbol, is_us=False)
        time_str = _format_hk_timestamp(ts) if ts else None
        source = "https://finance.yahoo.com/quote/" + yf_symbol
        results.append({
            "name": stock["name"],
            "code": stock["code"],
            "price": price,
            "timestamp": time_str,
            "source": source,
        })
        logger.info(f"yfinance: {stock['name']} ({yf_symbol}): {price}")
        time.sleep(0.3)
    return results


def fetch_us_etf_data(etfs):
    results = []
    for etf in etfs:
        symbol = etf["code"]
        price, ts = _fetch_yf_data(symbol, is_us=True)
        time_str = _format_us_timestamp(ts) if ts else None
        source = "https://finance.yahoo.com/quote/" + symbol
        results.append({
            "name": etf["name"],
            "code": etf["code"],
            "price": price,
            "timestamp": time_str,
            "source": source,
        })
        logger.info(f"yfinance: {etf['name']} ({symbol}): {price}")
        time.sleep(0.3)
    return results


def fetch_hk_etf_data(etfs):
    results = []
    for etf in etfs:
        yf_symbol = _hk_code_to_yf(etf["code"])
        price, ts = _fetch_yf_data(yf_symbol, is_us=False)
        time_str = _format_hk_timestamp(ts) if ts else None
        source = "https://finance.yahoo.com/quote/" + yf_symbol
        results.append({
            "name": etf["name"],
            "code": etf["code"],
            "price": price,
            "timestamp": time_str,
            "source": source,
        })
        logger.info(f"yfinance: {etf['name']} ({yf_symbol}): {price}")
        time.sleep(0.3)
    return results
