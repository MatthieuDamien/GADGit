#!/usr/bin/env python 

import os
import sys 
import requests
import datetime 
from ics import Calendar




astreinte_url = "https://webmail.ube.fr/home/ya0902du%40ube.fr/Astreinte%20bioinfo/?fmt=ics"

resp = requests.get(astreinte_url, auth=("ya0902du", ""), timeout=20)


print("HTTP", resp.status_code, resp.headers.get("Content-Type"))
head = resp.text[:120].replace("\n", "\\n")
print("HEAD:", head)

text = resp.text.lstrip()
if resp.status_code != 200 or not text.startswith("BEGIN:VCALENDAR"):
    raise RuntimeError("Ce n'est pas un ICS valide (probable page HTML de login). \
        Vérifie URL, encodage, ?fmt=ics et l'auth.")
cal = Calendar(text)

for ev in sorted(cal.events):
    print(ev.name, ev.begin, ev.end)