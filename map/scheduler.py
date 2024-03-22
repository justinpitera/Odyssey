from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .task import vatsim_update, metar_update
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        vatsim_update,
        trigger=IntervalTrigger(seconds=60), 
        id='task_vatsim_id', 
        replace_existing=False, 
    )
    scheduler.add_job(
        metar_update,
        trigger=IntervalTrigger(seconds=1800),  # 30 minutes
        id='task_metar_id', 
        replace_existing=False,
    )
    scheduler.start()

