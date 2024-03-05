from celery import shared_task
from .views import update_vatsim_controllers
from datetime import datetime, timedelta



@shared_task
def vatsim_update():
    current_time = datetime.now()

    nextUpdateTime = current_time + timedelta(minutes=10)

    update_vatsim_controllers(request=None)

    print("Updated VATSIM data. Next update at: ", nextUpdateTime.strftime("%H:%M:%S"))
