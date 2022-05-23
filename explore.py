import csv

with open('MH-Degree-plan-Muir-CS26.csv', newline='') as csvfile:
    readboi = csv.reader(csvfile, delimiter=' ', quotechar='|')
    for row in readboi:
        print(', '.join(row))