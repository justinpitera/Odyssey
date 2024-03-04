from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .task import vatsim_update
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        vatsim_update,
        trigger=IntervalTrigger(seconds=180),  # Run the task every 3 minutes
        id='your_unique_job_id',  # Unique ID for your job
        replace_existing=True,
    )
    scheduler.start()

