from celery import shared_task
from .views import update_vatsim_controllers
from map.weatherUtility import fetch_metars
from datetime import datetime, timedelta



@shared_task
def vatsim_update():
    current_time = datetime.now()
    update_vatsim_controllers(request=None)
    nextUpdateTime = current_time + timedelta(minutes=1)
    print("Updated VATSIM data. Next update at: ", nextUpdateTime.strftime("%H:%M:%S"))

@shared_task
def metar_update():
    current_time = datetime.now()
    fetch_metars(request=None)
    nextUpdateTime = current_time + timedelta(minutes=30)
    print("Updated METAR data. Next update at: ", nextUpdateTime.strftime("%H:%M:%S"))