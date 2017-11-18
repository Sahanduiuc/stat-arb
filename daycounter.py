from datetime import datetime


start = "2017-05-26"
end = "2017-11-10"

def days_between(d1, d2):
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    d2 = datetime.strptime(d2, "%Y-%m-%d")
    return abs((d2 - d1).days)

a = days_between(start,end)
print(a)