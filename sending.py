
import requests
import json
import datetime
from pytz import timezone
import time
import yaml




DISCORD_WEBHOOK_URL= "https://discord.com/api/webhooks/1006920205575917639/BSGjqy0N3XRspCzvxOimPggXwiU5S2uY-WVRF2wgs4EfxnupFqLnSPF9fsSpPirCJ6Oj"


msg="사랑해"

now = datetime.datetime.now()
message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
requests.post(DISCORD_WEBHOOK_URL, data=message)
print(message)