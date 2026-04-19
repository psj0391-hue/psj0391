import schedule
import time
from datetime import datetime
from krx import fetch_top10, fetch_weekly_top10, get_report_config, INVESTORS
from notify import send


def format_section(investor: str, df, label: str = "") -> str:
    title = f"<b>📊 {investor} 순매수 TOP10{label}</b>"
    if df.empty:
        return f"{title}\n데이터 없음"

    lines = [title]
    for rank, (_, row) in enumerate(df.iterrows(), 1):
        amount = int(row["순매수"]) // 1_000_000
        sign = "+" if amount >= 0 else ""
        lines.append(f"{rank}. {row['종목명']}  {sign}{amount:,}백만원")
    return "\n".join(lines)


def run():
    report_type, date_info = get_report_config()
    now = datetime.now()

    if report_type == "daily":
        date = date_info
        dt_str = datetime.strptime(date, "%Y%m%d").strftime("%Y년 %m월 %d일")
        header = f"📅 <b>{dt_str} 수급 리포트</b>"
        label = ""

        sections = [header]
        for investor in INVESTORS:
            try:
                df = fetch_top10(date, investor)
                sections.append(format_section(investor, df, label))
            except Exception as e:
                sections.append(f"[{investor}] 오류: {e}")

    else:  # weekly
        dates = date_info
        start = datetime.strptime(dates[0], "%Y%m%d").strftime("%m/%d")
        end   = datetime.strptime(dates[-1], "%Y%m%d").strftime("%m/%d")
        header = f"📅 <b>{start}~{end} 주간 수급 리포트</b>"
        label = " (주간합산)"

        sections = [header]
        for investor in INVESTORS:
            try:
                df = fetch_weekly_top10(dates, investor)
                sections.append(format_section(investor, df, label))
            except Exception as e:
                sections.append(f"[{investor}] 오류: {e}")

    send("\n\n".join(sections))
    print(f"[{now:%H:%M:%S}] {report_type} 리포트 전송 완료")


if __name__ == "__main__":
    print("KRX 수급 알림봇 시작")
    run()  # 시작 즉시 1회 실행

    # 주중 15:45 실행 (장 마감 직후)
    # 토/일에 수동 실행 시 주간 리포트 자동 전환
    schedule.every().monday.at("15:45").do(run)
    schedule.every().tuesday.at("15:45").do(run)
    schedule.every().wednesday.at("15:45").do(run)
    schedule.every().thursday.at("15:45").do(run)
    schedule.every().friday.at("15:45").do(run)

    while True:
        schedule.run_pending()
        time.sleep(60)
