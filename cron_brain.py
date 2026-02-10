
from molt_brain import run_single_cycle

if __name__ == "__main__":
    print("🕒 CRON JOB STARTED: Palimpsest Brain")
    result = run_single_cycle()
    print(f"🏁 CRON JOB FINISHED: {result}")
