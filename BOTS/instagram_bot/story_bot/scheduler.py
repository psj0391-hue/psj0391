"""
매일 18:00에 자동 실행하는 스케줄러
실행: py scheduler.py  (백그라운드로 켜두면 됨)
"""
import schedule, time
from main import run


def job():
    print("⏰ 18:00 - 테마 스토리 자동 실행")
    try:
        run()
    except Exception as e:
        print(f"오류 발생: {e}")


schedule.every().day.at("18:00").do(job)

print("스케줄러 시작 - 매일 18:00 실행 대기 중...")
print("종료하려면 Ctrl+C")

while True:
    schedule.run_pending()
    time.sleep(30)
