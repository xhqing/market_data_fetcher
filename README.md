# market-data-fetcher

MCP Server for fetching market data from Longport API and AKShare, supporting Hong Kong and US stock market data including indices, stocks, and ETFs.

## Features

- Fetch Hong Kong and US index data (HSI, HSTECH, HSCEI, S&P 500, Nasdaq 100, Dow Jones)
- Fetch Hong Kong stock data
- Fetch Hong Kong and US ETF data
- Support multiple data sources: Longport API, AKShare (Sina Finance)
- Automatic fallback from Longport to AKShare
- Configurable target list via `targets.json`

## Installation

### Basic Installation (AKShare only, free)

```bash
pip install market-data-fetcher
```

### With Longport SDK

```bash
pip install "market-data-fetcher[longport]"
```

### From Source

```bash
git clone https://github.com/xhqing/market_data_fetcher.git
cd market_data_fetcher
pip install -e .
```

With Longport SDK:

```bash
pip install -e ".[longport]"
```

## Quick Start

### 1. Create `targets.json`

Create a `targets.json` file in your project root directory to define which indices, stocks, and ETFs to track. See the [targets.json Configuration](#targetsjson-configuration) section for details.

### 2. Configure Environment Variables (Optional)

If you want to use Longport as a data source, set the following environment variables:

```bash
export LONGPORT_APP_KEY="your_app_key"
export LONGPORT_APP_SECRET="your_app_secret"
export LONGPORT_ACCESS_TOKEN="your_access_token"
```

If you only use AKShare (free, no registration required), you can skip this step.

### 3. Configure MCP in TRAE CN

In TRAE CN, you can add MCP Server through the GUI. Follow these steps:

#### Step 1: Open MCP Settings

- In **IDE mode**: Click the **Settings** icon in the top-right corner of the IDE, then select **MCP**.
- In **SOLO mode**: Click the **Settings** icon in the top-right corner of the AI chat panel, then select **MCP**.

#### Step 2: Add MCP Server Manually

1. In the MCP window, click the **+ Add** button in the top-right corner, then select **Manually Add** (手动添加).
2. The **Manual Configuration** (手动配置) window will appear.
3. Paste the following JSON configuration into the input box:

**Using `uvx` (recommended, no installation required):**

```json
{
  "mcpServers": {
    "market-data-fetcher": {
      "command": "uvx",
      "args": ["market-data-fetcher"],
      "env": {
        "LONGPORT_APP_KEY": "your_app_key",
        "LONGPORT_APP_SECRET": "your_app_secret",
        "LONGPORT_ACCESS_TOKEN": "your_access_token",
        "TARGETS_JSON_PATH": "/absolute/path/to/your/project/targets.json"
      }
    }
  }
}
```

**Using `python -m` (requires pip install first):**

```json
{
  "mcpServers": {
    "market-data-fetcher": {
      "command": "python",
      "args": ["-m", "market_data_fetcher.server"],
      "env": {
        "LONGPORT_APP_KEY": "your_app_key",
        "LONGPORT_APP_SECRET": "your_app_secret",
        "LONGPORT_ACCESS_TOKEN": "your_access_token",
        "TARGETS_JSON_PATH": "/absolute/path/to/your/project/targets.json"
      }
    }
  }
}
```

**Using entry point command (requires pip install first):**

```json
{
  "mcpServers": {
    "market-data-fetcher": {
      "command": "market-data-fetcher",
      "env": {
        "LONGPORT_APP_KEY": "your_app_key",
        "LONGPORT_APP_SECRET": "your_app_secret",
        "LONGPORT_ACCESS_TOKEN": "your_access_token",
        "TARGETS_JSON_PATH": "/absolute/path/to/your/project/targets.json"
      }
    }
  }
}
```

4. Click **Confirm** (确认) button.

> **Notes**:
> - Replace `your_app_key`, `your_app_secret`, `your_access_token` with your actual Longport credentials. If you only use AKShare (free), you can omit the `LONGPORT_*` environment variables.
> - Replace `/absolute/path/to/your/project/targets.json` with the actual absolute path to your `targets.json` file. You can also use `${workspaceFolder}/targets.json` to reference the current project root.
> - If you use `uvx`, make sure [uv](https://github.com/astral-sh/uv) is installed. Install with: `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux) or `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows).
> - If you use `python` or `market-data-fetcher` command, make sure the package is installed first (`pip install market-data-fetcher` or `pip install -e .`).

#### Step 3: Add MCP Server to Agent

After adding the MCP Server, you need to add it to an agent to use it:

- **Built-in Agent**: The MCP Server will be automatically added to the built-in **Builder with MCP** agent.
- **Custom Agent**: You can add the MCP Server to a custom agent by:
  1. Going to the MCP Server list.
  2. Clicking the **+** button on the right side of the target MCP Server.
  3. Selecting the agent(s) you want to add the MCP Server to.
  4. Clicking **Confirm** (确认).

  Alternatively, when creating a new custom agent, you can add MCP Servers in the **Tools** (工具) section of the agent creation panel.

#### Step 4: Verify Configuration

After adding the MCP Server, check that a green checkmark (✓) appears next to it in the MCP list, indicating it is running properly. If a red cross (✗) appears, check the configuration and logs for errors.

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LONGPORT_APP_KEY` | Longport API App Key | For Longport source | Empty |
| `LONGPORT_APP_SECRET` | Longport API App Secret | For Longport source | Empty |
| `LONGPORT_ACCESS_TOKEN` | Longport API Access Token | For Longport source | Empty |
| `TARGETS_JSON_PATH` | Absolute path to `targets.json` | Optional | `<cwd>/targets.json` |

### targets.json Configuration

The `targets.json` file defines which market instruments to track. It is divided into two sections: `hk_shares` (Hong Kong market) and `us_shares` (US market).

#### Full Example

```json
{
  "hk_shares": {
    "index_major": [
      { "name": "恒生指数", "code": "HSI" },
      { "name": "恒生科技指数", "code": "HSTECH" },
      { "name": "国企指数", "code": "HSCEI" }
    ],
    "index_sector": [],
    "hkex_stocks": [
      { "name": "腾讯控股", "code": "00700.HK" },
      { "name": "阿里巴巴", "code": "09988.HK" },
      { "name": "美团", "code": "03690.HK" },
      { "name": "小米集团", "code": "01810.HK" },
      { "name": "比亚迪", "code": "01211.HK" }
    ],
    "hkex_etf": [
      { "name": "盈富基金", "code": "02800.HK" },
      { "name": "恒生科技ETF", "code": "03033.HK" },
      { "name": "南方两倍看空恒指", "code": "07500.HK" }
    ]
  },
  "us_shares": {
    "index_major": [
      { "name": "纳斯达克100指数", "code": ".NDX" },
      { "name": "标普500指数", "code": ".SPX" },
      { "name": "道琼斯工业指数", "code": ".DJI" }
    ],
    "etf": [
      { "name": "QQQ", "code": "QQQ" },
      { "name": "SPY", "code": "SPY" }
    ]
  }
}
```

#### Field Descriptions

**`hk_shares` section:**

| Field | Type | Description |
|-------|------|-------------|
| `index_major` | Array | Major Hong Kong indices. For AKShare source, supported codes: `HSI`, `HSTECH`, `HSCEI`. For Longport source, use the corresponding Longport symbol codes. |
| `index_sector` | Array | Sector indices. Same format as `index_major`. |
| `hkex_stocks` | Array | Hong Kong Stock Exchange listed stocks. Code format: `XXXXX.HK` (e.g., `00700.HK`). |
| `hkex_etf` | Array | Hong Kong listed ETFs. Code format: `XXXXX.HK` (e.g., `02800.HK`). |

**`us_shares` section:**

| Field | Type | Description |
|-------|------|-------------|
| `index_major` | Array | Major US indices. For AKShare source, supported codes: `.NDX`, `.SPX`, `.DJI`. For Longport source, use the corresponding Longport symbol codes. |
| `etf` | Array | US listed ETFs. Code format: ticker symbol (e.g., `QQQ`, `SPY`). |

**Each item format:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Display name of the instrument (e.g., `"腾讯控股"`) |
| `code` | String | Instrument code. Format varies by market and data source. |

#### Code Format Notes

- **Hong Kong stocks/ETFs**: Use `XXXXX.HK` format (5-digit code with `.HK` suffix), e.g., `00700.HK`
- **Hong Kong indices (AKShare)**: Use short codes `HSI`, `HSTECH`, `HSCEI`
- **US indices (AKShare)**: Use `.NDX`, `.SPX`, `.DJI`
- **US ETFs**: Use ticker symbol directly, e.g., `QQQ`, `SPY`
- **Longport codes**: Follow Longport's symbol format (typically same as above for HK/US)

## MCP Tools

### `fetch_index_data`

Fetch latest index data for Hong Kong and US markets.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | String | `"longport"` | Data source: `"longport"`, `"akshare"`, or `"both"` |

**Returns:** JSON string containing index data with fields: `name`, `code`, `price`, `timestamp`, `source`.

**Example response:**

```json
{
  "data": [
    { "name": "恒生指数", "code": "HSI", "price": 22423.02, "timestamp": "2025-05-01 16:00:00 (北京时间)", "source": "AKShare" },
    { "name": "标普500指数", "code": ".SPX", "price": 5604.14, "timestamp": "2025-05-01 16:00:00 (美东时间)", "source": "AKShare" }
  ],
  "count": 2
}
```

### `fetch_stock_data`

Fetch latest stock data for Hong Kong stocks.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `codes` | List[String] or null | `null` | Optional list of stock codes to fetch (e.g., `["00700.HK", "09988.HK"]`). If not provided, fetches all stocks from `targets.json`. |
| `source` | String | `"longport"` | Data source: `"longport"` or `"akshare"` |

**Returns:** JSON string containing stock data with fields: `name`, `code`, `price`, `timestamp`, `source`.

### `fetch_etf_data`

Fetch latest ETF data for Hong Kong and US ETFs.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `codes` | List[String] or null | `null` | Optional list of ETF codes to fetch (e.g., `["02800.HK", "03033.HK"]`). If not provided, fetches all ETFs from `targets.json`. |
| `source` | String | `"longport"` | Data source: `"longport"` or `"akshare"` |

**Returns:** JSON string containing ETF data with fields: `name`, `code`, `price`, `timestamp`, `source`.

### `fetch_all_market_data`

Fetch all market data at once: indices, stocks, and ETFs.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | String | `"longport"` | Data source: `"longport"`, `"akshare"`, or `"both"` |

**Returns:** JSON string containing all market data grouped by type (`index_data`, `stock_data`, `etf_data`).

### `get_targets_config`

Read and return the current `targets.json` configuration.

**Parameters:** None

**Returns:** JSON string of the `targets.json` content.

### `check_longport_status`

Check if Longport SDK is available and credentials are configured.

**Parameters:** None

**Returns:** JSON string with availability status and credential check results.

**Example response:**

```json
{
  "sdk_installed": true,
  "credentials": {
    "app_key": "configured",
    "app_secret": "configured",
    "access_token": "configured"
  },
  "ready": true
}
```

## Data Sources

### AKShare (Free)

- No registration or API key required
- Data sourced from Sina Finance
- Supports Hong Kong indices (HSI, HSTECH, HSCEI), US indices (.NDX, .SPX, .DJI), Hong Kong stocks and ETFs
- May have rate limiting; built-in delays between requests

### Longport API

- Requires Longport account and API credentials ([Register here](https://longportapp.com/))
- Real-time and historical market data
- Broader instrument coverage
- Install with: `pip install longport`

### Fallback Strategy (`source="both"`)

When using `source="both"`, the server first tries Longport for all instruments. For any instruments where Longport fails to return a price, it falls back to AKShare to fill in the gaps.

## Usage in Trae IDE

Once the MCP server is configured in `.trae/mcp.json`, you can interact with it through the AI assistant in Trae IDE. For example:

- "帮我获取港股和美股的最新指数数据"
- "查询腾讯和阿里巴巴的最新股价"
- "获取所有ETF数据"
- "检查Longport的连接状态"
- "查看当前的targets配置"

The AI assistant will automatically call the appropriate MCP tools to fetch the data.

## Running Standalone

You can also run the MCP server directly from the command line:

```bash
# If installed via pip
market-data-fetcher

# Or using Python module
python -m market_data_fetcher.server
```

## License

AGPL-3.0
