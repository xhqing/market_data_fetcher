import logging
import time
from datetime import datetime, timezone

import pytz

from market_data_fetcher.config import get_longport_credentials

logger = logging.getLogger(__name__)

LONGPORT_AVAILABLE = False
try:
    from longport.openapi import QuoteContext, Config, Period, AdjustType

    LONGPORT_AVAILABLE = True
    logger.info("Longport SDK available")
except ImportError:
    logger.warning("Longport SDK not available, install with: pip install longport")


def is_available():
    return LONGPORT_AVAILABLE


def _create_context():
    if not LONGPORT_AVAILABLE:
        return None
    creds = get_longport_credentials()
    if not all(creds.values()):
        logger.error("Longport credentials not configured")
        return None
    try:
        config = Config(
            app_key=creds["app_key"],
            app_secret=creds["app_secret"],
            access_token=creds["access_token"],
        )
        ctx = QuoteContext(config)
        logger.info("Longport context created successfully")
        return ctx
    except Exception as e:
        logger.error(f"Failed to create Longport context: {e}")
        return None


def _format_timestamp(ts, is_us_index=False):
    try:
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            if is_us_index:
                local_tz = pytz.timezone("US/Eastern")
                dt_local = dt.astimezone(local_tz)
                return dt_local.strftime("%Y-%m-%d %H:%M:%S") + " (美东时间)"
            else:
                local_tz = pytz.timezone("Asia/Shanghai")
                dt_local = dt.astimezone(local_tz)
                return dt_local.strftime("%Y-%m-%d %H:%M:%S") + " (北京时间)"
        elif hasattr(ts, "year"):
            dt = ts
            if is_us_index:
                if dt.tzinfo is None:
                    dt = pytz.timezone("US/Eastern").localize(dt)
                return dt.strftime("%Y-%m-%d %H:%M:%S") + " (美东时间)"
            else:
                if dt.tzinfo is None:
                    dt = pytz.timezone("Asia/Shanghai").localize(dt)
                return dt.strftime("%Y-%m-%d %H:%M:%S") + " (北京时间)"
        else:
            return str(ts)
    except Exception:
        return str(ts)


US_INDEX_NAMES = {"纳斯达克100指数", "标普500指数", "道琼斯工业指数", "道琼斯指数"}


def _is_us_index(name):
    return name in US_INDEX_NAMES


def fetch_stock_data(ctx, symbol):
    if ctx is None:
        return None, None, "Longport API"
    price = None
    ts = None
    source = "Longport API"
    try:
        quotes = ctx.quote([symbol])
        if quotes:
            q = quotes[0]
            price = round(float(q.last_done), 2)
            ts = q.timestamp
            if ts is not None and hasattr(ts, "hour") and ts.hour == 0 and ts.minute == 0 and ts.second == 0:
                ts = None
        if price is None:
            try:
                candles = ctx.candlesticks(symbol, Period.Day, 1, AdjustType.NoAdjust)
                if candles:
                    latest = candles[-1]
                    price = round(float(latest.close), 2)
                    ts = latest.timestamp
            except Exception as e:
                logger.warning(f"Longport candlestick also failed for {symbol}: {e}")
    except Exception as e:
        logger.warning(f"Longport quote failed for {symbol}: {e}")
        try:
            candles = ctx.candlesticks(symbol, Period.Day, 1, AdjustType.NoAdjust)
            if candles:
                latest = candles[-1]
                price = round(float(latest.close), 2)
                ts = latest.timestamp
        except Exception as e2:
            logger.warning(f"Longport candlestick failed for {symbol}: {e2}")
    return price, ts, source


def fetch_batch_quotes(ctx, symbols):
    if ctx is None:
        return {}
    results = {}
    try:
        quotes = ctx.quote(symbols)
        for q in quotes:
            results[q.symbol] = {
                "price": float(q.last_done),
                "timestamp": q.timestamp,
            }
        logger.info(f"Longport: Got quotes for {len(results)} symbols")
    except Exception as e:
        logger.warning(f"Longport batch quote failed: {e}")
        for i in range(0, len(symbols), 5):
            batch = symbols[i : i + 5]
            try:
                quotes = ctx.quote(batch)
                for q in quotes:
                    results[q.symbol] = {
                        "price": float(q.last_done),
                        "timestamp": q.timestamp,
                    }
                time.sleep(0.5)
            except Exception as e2:
                logger.warning(f"Longport batch quote failed for {batch}: {e2}")
    return results


def fetch_index_data(indices):
    ctx = _create_context()
    if ctx is None:
        return [{"name": idx["name"], "code": idx["code"], "price": None, "timestamp": None, "source": "Longport API (unavailable)", "error": "Longport SDK not available or credentials not configured"} for idx in indices]

    results = []
    for idx in indices:
        is_us = _is_us_index(idx["name"])
        price, ts, source = fetch_stock_data(ctx, idx["code"])
        time_str = _format_timestamp(ts, is_us) if ts else None
        results.append({
            "name": idx["name"],
            "code": idx["code"],
            "price": price,
            "timestamp": time_str,
            "source": source,
        })
        time.sleep(0.3)

    return results


def fetch_stock_list_data(stocks):
    ctx = _create_context()
    if ctx is None:
        return [{"name": s["name"], "code": s["code"], "price": None, "timestamp": None, "source": "Longport API (unavailable)", "error": "Longport SDK not available or credentials not configured"} for s in stocks]

    results = []
    for stock in stocks:
        price, ts, source = fetch_stock_data(ctx, stock["code"])
        time_str = _format_timestamp(ts, False) if ts else None
        results.append({
            "name": stock["name"],
            "code": stock["code"],
            "price": price,
            "timestamp": time_str,
            "source": source,
        })
        time.sleep(0.3)

    return results


def fetch_etf_list_data(etfs):
    ctx = _create_context()
    if ctx is None:
        return [{"name": e["name"], "code": e["code"], "price": None, "timestamp": None, "source": "Longport API (unavailable)", "error": "Longport SDK not available or credentials not configured"} for e in etfs]

    results = []
    for etf in etfs:
        is_us = not etf["code"].endswith(".HK")
        price, ts, source = fetch_stock_data(ctx, etf["code"])
        time_str = _format_timestamp(ts, is_us) if ts else None
        results.append({
            "name": etf["name"],
            "code": etf["code"],
            "price": price,
            "timestamp": time_str,
            "source": source,
        })
        time.sleep(0.3)

    return results
