import datetime as dt

import pandas as pd
from icalendar import Calendar, Event
from icalendar.prop import vDate

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

cal = Calendar()
allDateTasks = []
for exp, weeks in experiments.items():
    for week, dailyTasks in weeks.items():
        for date, task in zip(*[dates[week], dailyTasks]):
            if pd.notna(task):
                event = Event()
                event.add("summary", f"{exp} - {task}")
                event.add("dtstart", vDate(date))
                event.add("dtend", vDate(date + dt.timedelta(days=1)))
                event.add("sequence", 1)
                cal.add_component(event)

with open(f"Experiments.ics", "w") as f:
    f.write(cal.to_ical().decode("utf-8"))
