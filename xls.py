import csv

with open('/home/uad/Programming/cryptocurrency/arbitrage/stat-arb/stat-results/BTCUSD-2017-01-02--2017-11-01', 'r') as in_file:
    stripped = (line.strip() for line in in_file)
    lines = (line.split(",") for line in stripped if line)
    with open('log.csv', 'w') as out_file:
        writer = csv.writer(out_file)
        writer.writerow(('title', 'intro'))
        writer.writerows(lines)