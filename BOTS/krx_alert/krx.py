import os
import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

APP_KEY    = os.getenv("KIS_APP_KEY", "").strip()
APP_SECRET = os.getenv("KIS_APP_SECRET", "").strip()
BASE_URL   = "https://openapi.koreainvestment.com:9443"
TOKEN_FILE = Path(__file__).parent / ".token_cache.json"

INVESTORS = {"외국인": "1", "기관합계": "2", "연기금등": "3"}


# ── 토큰 ──────────────────────────────────────────────
def get_access_token() -> str:
    if TOKEN_FILE.exists():
        cache = json.loads(TOKEN_FILE.read_text())
        if time.time() < cache.get("expires_at", 0):
            return cache["token"]

    r = requests.post(
        f"{BASE_URL}/oauth2/tokenP",
        json={"grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    if "access_token" not in data:
        raise RuntimeError(f"토큰 발급 실패: {data}")

    TOKEN_FILE.write_text(
        json.dumps({"token": data["access_token"], "expires_at": time.time() + 82800})
    )
    return data["access_token"]


def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_access_token()}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "HHKDB669100C0",
    }


# ── 날짜 판단 ─────────────────────────────────────────
def get_report_config() -> tuple[str, str | list[str]]:
    """
    반환: (report_type, date_or_dates)
      - ("daily", "YYYYMMDD")   → 화~금, 월
      - ("weekly", ["YYYYMMDD", ...])  → 토, 일
    """
    today = datetime.now()
    wd = today.weekday()  # 0=월 1=화 … 5=토 6=일

    if wd == 0:  # 월요일 → 직전 금요일
        target = today - timedelta(days=3)
        return "daily", target.strftime("%Y%m%d")

    elif 1 <= wd <= 4:  # 화~금 → 전날
        target = today - timedelta(days=1)
        return "daily", target.strftime("%Y%m%d")

    else:  # 토(5), 일(6) → 이번주 월~금
        monday = today - timedelta(days=wd)
        dates = [(monday + timedelta(days=i)).strftime("%Y%m%d") for i in range(5)]
        return "weekly", dates


# ── 데이터 조회 ───────────────────────────────────────
def _fetch_raw(start: str, end: str, investor: str, market: str = "KOSPI") -> pd.DataFrame:
    params = {
        "FID_COND_MRKT_DIV_CODE": "J" if market == "KOSPI" else "Q",
        "FID_COND_SCR_DIV_CODE": "20001",
        "FID_INPUT_ISCD": "0001",
        "FID_DIV_CLS_CODE": "0",
        "FID_RANK_SORT_CLS_CODE": "0",
        "FID_ETC_CLS_CODE": "0",
        "CTS": "",
        "GB1": INVESTORS.get(investor, "1"),
        "F_DT": start,
        "T_DT": end,
        "SHT_CD": "",
    }
    r = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/quotations/foreign-institution-total",
        headers=_headers(),
        params=params,
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()

    if data.get("rt_cd") != "0":
        raise RuntimeError(data.get("msg1", "KIS API 오류"))

    rows = data.get("output1", data.get("output", []))
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def fetch_top10(date: str, investor: str, market: str = "KOSPI") -> pd.DataFrame:
    """단일 날짜 TOP10"""
    df = _fetch_raw(date, date, investor, market)
    return _to_top10(df)


def fetch_weekly_top10(dates: list[str], investor: str, market: str = "KOSPI") -> pd.DataFrame:
    """주간(월~금) 합산 TOP10"""
    frames = []
    for d in dates:
        try:
            df = _fetch_raw(d, d, investor, market)
            if not df.empty:
                frames.append(df)
        except Exception:
            pass

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)

    name_col   = _find_col(combined, ["isnm", "nm"])
    netbuy_col = _find_col(combined, ["ntby"])

    if not name_col or not netbuy_col:
        return pd.DataFrame()

    combined[netbuy_col] = pd.to_numeric(combined[netbuy_col], errors="coerce").fillna(0)
    agg = combined.groupby(name_col)[netbuy_col].sum().reset_index()
    agg = agg.sort_values(netbuy_col, ascending=False).head(10)
    agg.columns = ["종목명", "순매수"]
    agg.index = range(1, len(agg) + 1)
    return agg


# ── 내부 유틸 ─────────────────────────────────────────
def _find_col(df: pd.DataFrame, keywords: list[str]) -> str | None:
    for kw in keywords:
        col = next((c for c in df.columns if kw in c.lower()), None)
        if col:
            return col
    return None


def _to_top10(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    name_col   = _find_col(df, ["isnm", "nm"])
    netbuy_col = _find_col(df, ["ntby"])

    if not name_col or not netbuy_col:
        print(f"[DEBUG] 컬럼 목록: {df.columns.tolist()}")
        print(f"[DEBUG] 첫 행: {df.iloc[0].to_dict()}")
        return pd.DataFrame()

    df = df.copy()
    df[netbuy_col] = pd.to_numeric(df[netbuy_col], errors="coerce")
    df = df[df[netbuy_col] > 0].sort_values(netbuy_col, ascending=False).head(10)
    result = df[[name_col, netbuy_col]].copy()
    result.columns = ["종목명", "순매수"]
    result.index = range(1, len(result) + 1)
    return result
