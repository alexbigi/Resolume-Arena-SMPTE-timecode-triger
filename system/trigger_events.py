import threading
import time
import requests
import json

from system.log_instance import LogInstance


class TriggerEvent:
    id: int
    name: str
    api_call: str
    type: str

    timecode_trigger: str
    is_runned: bool

    def __init__(self, **kwargs):
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])


class TriggerEvents:
    base_url: str = "http://127.0.0.1:8080/api/v1"

    events: list[TriggerEvent] = [
        TriggerEvent(
            id=1,
            name="first clip",
            api_call="/composition/layers/1/clips/1/connect",
            timecode_trigger="00:00:01:00",
            type="resolume_type",
            is_runned=False
        ),
        TriggerEvent(
            id=2,
            name="second clip",
            api_call="/composition/layers/1/clips/2/connect",
            timecode_trigger="00:00:06:00",
            type="resolume_type",
            is_runned=False
        ),
        TriggerEvent(
            id=3,
            name="third clip",
            api_call="/composition/layers/1/clips/3/connect",
            timecode_trigger="00:00:10:00",
            type="resolume_type",
            is_runned=False
        ),
    ]

    def trigger_run(self, event: TriggerEvent):
        if not event.is_runned:
            event.is_runned = True
            t = threading.Thread(target=self.call_api, args=(event, ), daemon=True)
            t.start()

    def call_api(self, event: TriggerEvent):
        try:
            r = requests.post(self.base_url + event.api_call, data=json.dumps(True))
            LogInstance.string_data += event.name + "\n"
            LogInstance.string_data += event.timecode_trigger + "\n"
            LogInstance.string_data += event.api_call + "\n"
            LogInstance.string_data += "\n"
            print(r.status_code, r.reason, r.request.body)
            time.sleep(.1)
            r = requests.post(self.base_url + event.api_call, data=json.dumps(False))
            print(r.status_code, r.reason, r.request.body)
        except Exception:
            LogInstance.string_data += self.base_url + " connection error!" + "\n"
            LogInstance.string_data += "\n"
