import logging
import time
from datetime import datetime

import akshare as ak
import pytz

logger = logging.getLogger(__name__)

bj_tz = pytz.timezone("Asia/Shanghai")
us_eastern_tz = pytz.timezone("US/Eastern")

HK_INDEX_MAP = {
    "HSI": "恒生指数",
    "HSTECH": "恒生科技指数",
    "HSCEI": "国企指数",
}

US_INDICES = [
    {"name": "纳斯达克100指数", "code": ".NDX", "sina_code": ".NDX"},
    {"name": "标普500指数", "code": ".SPX", "sina_code": ".INX"},
    {"name": "道琼斯工业指数", "code": ".DJI", "sina_code": ".DJI"},
]


def _format_hk_timestamp(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        dt_bj = bj_tz.localize(dt.replace(hour=16, minute=0, second=0))
        return dt_bj.strftime("%Y-%m-%d %H:%M:%S") + " (北京时间)"
    except Exception:
        return date_str + " 16:00:00 (北京时间)"


def _format_us_timestamp(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        dt_us = us_eastern_tz.localize(dt.replace(hour=16, minute=0, second=0))
        return dt_us.strftime("%Y-%m-%d %H:%M:%S") + " (美东时间)"
    except Exception:
        return date_str + " 16:00:00 (美东时间)"


def fetch_hk_index_data():
    results = []
    for code, name in HK_INDEX_MAP.items():
        try:
            df = ak.stock_hk_index_daily_sina(symbol=code)
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                close_price = float(latest["close"])
                date_str = str(latest["date"])
                time_str = _format_hk_timestamp(date_str)
                source = "https://cn.stockq.org/index/" + code + ".php"
                results.append({
                    "name": name,
                    "code": code,
                    "price": close_price,
                    "timestamp": time_str,
                    "source": source,
                })
                logger.info(f"AKShare: {name}: {close_price} ({date_str})")
            else:
                results.append({"name": name, "code": code, "price": None, "timestamp": None, "source": "", "error": "empty data"})
                logger.warning(f"AKShare: {name}: empty data")
        except Exception as e:
            results.append({"name": name, "code": code, "price": None, "timestamp": None, "source": "", "error": str(e)})
            logger.warning(f"AKShare: {name}: {e}")
        time.sleep(0.5)
    return results


def fetch_us_index_data():
    results = []
    for idx in US_INDICES:
        try:
            df = ak.index_us_stock_sina(symbol=idx["sina_code"])
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                close_price = float(latest["close"])
                date_str = str(latest["date"])
                time_str = _format_us_timestamp(date_str)
                yahoo_code = idx["code"].replace(".", "%5E")
                source = "https://finance.yahoo.com/quote/" + yahoo_code
                results.append({
                    "name": idx["name"],
                    "code": idx["code"],
                    "price": close_price,
                    "timestamp": time_str,
                    "source": source,
                })
                logger.info(f"AKShare: {idx['name']}: {close_price} ({date_str})")
            else:
                results.append({"name": idx["name"], "code": idx["code"], "price": None, "timestamp": None, "source": "", "error": "empty data"})
                logger.warning(f"AKShare: {idx['name']}: empty data")
        except Exception as e:
            results.append({"name": idx["name"], "code": idx["code"], "price": None, "timestamp": None, "source": "", "error": str(e)})
            logger.warning(f"AKShare: {idx['name']}: {e}")
        time.sleep(0.5)
    return results


def fetch_hk_stock_data(stocks):
    results = []
    for stock in stocks:
        name = stock["name"]
        code = stock["code"]
        ak_code = code.replace(".HK", "")
        try:
            df = ak.stock_hk_daily(symbol=ak_code, adjust="qfq")
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                close_price = float(latest["close"])
                date_str = str(latest["date"])
                time_str = _format_hk_timestamp(date_str)
                source = "https://www.aastocks.com/sc/cnhk/quote/quote.aspx?symbol=" + ak_code
                results.append({
                    "name": name,
                    "code": code,
                    "price": close_price,
                    "timestamp": time_str,
                    "source": source,
                })
                logger.info(f"AKShare: {name} ({code}): {close_price} ({date_str})")
            else:
                results.append({"name": name, "code": code, "price": None, "timestamp": None, "source": "", "error": "empty data"})
                logger.warning(f"AKShare: {name} ({code}): empty data")
        except Exception as e:
            results.append({"name": name, "code": code, "price": None, "timestamp": None, "source": "", "error": str(e)[:100]})
            logger.warning(f"AKShare: {name} ({code}): {str(e)[:60]}")
        time.sleep(0.3)
    return results


def fetch_hk_etf_data(etfs):
    results = []
    for etf in etfs:
        name = etf["name"]
        code = etf["code"]
        ak_code = code.replace(".HK", "")
        try:
            df = ak.stock_hk_daily(symbol=ak_code, adjust="qfq")
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                close_price = float(latest["close"])
                date_str = str(latest["date"])
                time_str = _format_hk_timestamp(date_str)
                source = "https://www.aastocks.com/sc/cnhk/quote/quote.aspx?symbol=" + ak_code
                results.append({
                    "name": name,
                    "code": code,
                    "price": close_price,
                    "timestamp": time_str,
                    "source": source,
                })
                logger.info(f"AKShare: {name} ({code}): {close_price} ({date_str})")
            else:
                results.append({"name": name, "code": code, "price": None, "timestamp": None, "source": "", "error": "empty data"})
                logger.warning(f"AKShare: {name} ({code}): empty data")
        except Exception as e:
            results.append({"name": name, "code": code, "price": None, "timestamp": None, "source": "", "error": str(e)[:100]})
            logger.warning(f"AKShare: {name} ({code}): {str(e)[:60]}")
        time.sleep(0.3)
    return results


def fetch_all_index_data():
    hk_results = fetch_hk_index_data()
    us_results = fetch_us_index_data()
    return hk_results + us_results
