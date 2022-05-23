import csv

# read
with open('MH-Degree-plan-Muir-CS26.csv', newline='') as csvfile:
    readboi = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in readboi:
        print(', '.join(row))
# write
with open('MH-Degree-plan-Muir-CS26AUTOMATED.csv', 'w', newline='') as csvfile:
    writeboi = csv.writer(csvfile, delimiter=',', quotechar = '"', quoting=csv.QUOTE_MINIMAL)
    writeboi.writerow(['Curriculum'] + ['Computer Science'] + ['']*9)
    writeboi.writerow(['Degree Plan', 'Computer Science/ Muir'] + ['']*9)
    writeboi.writerow(['Institution', 'University of California, San Diego']+['']*9)
    writeboi.writerow(['Course ID','Course Name','Prefix','Number','Prerequisites','Corequisites','Strict-Corequisites','Credit Hours','Institution','Canonical Name','Term'])