import uuid
import datetime

import numpy as np
import pandas as pd

df = pd.read_excel("experimentalSetup.xlsx")  # , index_col=0)

dates = {}
for index, row in enumerate(df["dates"]):
    if pd.notna(row):
        dates[index] = list(df.loc[index][1:])
    else:
        break

experimentHeaders = {}
for index, row in enumerate(df["dates"]):
    if pd.notna(row) and "Week" not in row:
        experimentHeaders[row] = index

experiments = {}
for exp, index in experimentHeaders.items():
    currExp = {}
    temp = index + 1
    while temp < df.shape[0] and "Week" in str(df.loc[temp][0]):
        currExp[temp - index - 1] = list(df.loc[temp][1:])
        temp += 1
    experiments[df.loc[index][0]] = currExp


def makeCalendar(exp, dateTaskTuples):
    events = f"""
BEGIN:CALENDAR
VERSION:2.0
CALSCALE:GREGORIAN
PRODID:-//SabreDAV//SabreDAV//EN
X-WR-CALNAME:{exp}
REFRESH-INTERVAL;VALUE=DURATION:PT4H
X-PUBLISHED-TTL:PT4H
BEGIN:VTIMEZONE
TZID:America/New_York
BEGIN:DAYLIGHT
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
DTSTART:19700308T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
DTSTART:19701101T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
END:VTIMEZONE"""
    for date, task in dateTaskTuples:
        events += makeEvent(date, task)
    events += "\nEND:VCALENDAR"
    with open(f"{exp}.ics", "w") as f:
        f.write(events)


def makeEvent(date, task):
    fmtDate = lambda d: d.isoformat().replace(":", "").replace("-", "")
    return f"""
BEGIN:VEVENT
DTSTART;TZID=America/New_York:{fmtDate(date.date())}
DTEND;TZID=America/New_York:{fmtDate(date.date())}
SUMMARY:{task}
UID:{uuid.uuid4()}
CREATED:{fmtDate(datetime.datetime.now().replace(second=0, microsecond=0))}
DTSTAMP:{fmtDate(datetime.datetime.now().replace(second=0, microsecond=0))}
END:VEVENT"""


allDateTasks = []
for exp, weeks in experiments.items():
    tasks = []
    for week, dailyTasks in weeks.items():
        for date, task in zip(*[dates[week], dailyTasks]):
            if pd.notna(task):
                tasks.append((date, task))
                allDateTasks.append((date, f"{exp}: {task}"))
    # old method: make a calendar for each experiment instead of one combined calendar
    # makeCalendar(exp, tasks)

makeCalendar("Experiments", allDateTasks)
