import os
import json
import logging

logger = logging.getLogger(__name__)

DEFAULT_TARGETS_PATH = os.path.join(os.getcwd(), "targets.json")


def get_longport_credentials():
    app_key = os.environ.get("LONGPORT_APP_KEY", "")
    app_secret = os.environ.get("LONGPORT_APP_SECRET", "")
    access_token = os.environ.get("LONGPORT_ACCESS_TOKEN", "")
    if not all([app_key, app_secret, access_token]):
        logger.warning("Longport credentials not fully configured in environment variables")
    return {
        "app_key": app_key,
        "app_secret": app_secret,
        "access_token": access_token,
    }


def get_targets_path():
    return os.environ.get("TARGETS_JSON_PATH", DEFAULT_TARGETS_PATH)


def load_targets_config(targets_path=None):
    if targets_path is None:
        targets_path = get_targets_path()
    if not os.path.exists(targets_path):
        logger.warning(f"targets.json not found at {targets_path}")
        return {
            "hk_shares": {"index_major": [], "index_sector": [], "hkex_stocks": [], "hkex_etf": []},
            "us_shares": {"index_major": [], "etf": []},
        }
    with open(targets_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    logger.info(f"Loaded targets config from {targets_path}")
    return config


def get_indices_from_config(config):
    indices = []
    hk_shares = config.get("hk_shares", {})
    for idx in hk_shares.get("index_major", []):
        if idx.get("name") and idx.get("code"):
            indices.append({"name": idx["name"], "code": idx["code"]})
    for idx in hk_shares.get("index_sector", []):
        if idx.get("name") and idx.get("code"):
            indices.append({"name": idx["name"], "code": idx["code"]})
    us_shares = config.get("us_shares", {})
    for idx in us_shares.get("index_major", []):
        if idx.get("name") and idx.get("code"):
            indices.append({"name": idx["name"], "code": idx["code"]})
    return indices


def get_stocks_from_config(config):
    stocks = []
    hk_shares = config.get("hk_shares", {})
    for stock in hk_shares.get("hkex_stocks", []):
        if stock.get("name") and stock.get("code"):
            stocks.append({"name": stock["name"], "code": stock["code"]})
    return stocks


def get_etfs_from_config(config):
    etfs = []
    hk_shares = config.get("hk_shares", {})
    for etf in hk_shares.get("hkex_etf", []):
        if etf.get("name") and etf.get("code"):
            etfs.append({"name": etf["name"], "code": etf["code"]})
    us_shares = config.get("us_shares", {})
    for etf in us_shares.get("etf", []):
        if etf.get("name") and etf.get("code"):
            etfs.append({"name": etf["name"], "code": etf["code"]})
    return etfs
