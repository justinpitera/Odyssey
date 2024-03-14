from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .task import vatsim_update
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        vatsim_update,
        trigger=IntervalTrigger(seconds=60), 
        id='task_vatsim_id', 
        replace_existing=False, 
    )
    scheduler.start()

