import csv
from collections import Counter

input_file = '/Volumes/Test36/CSVs_to_ingest/123rfCSVs/CSV_NOKEYS.csv'
output_file = '/Volumes/Test36/CSVs_to_ingest/123rfCSVs/CSV_NOKEYS_unique.csv'

# Read the CSV file and extract the second column
keywords = []
with open(input_file, 'r', newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) >= 2:  # Make sure the row has at least two columns
            keywords.append(row[1])

# Count the occurrences of each keyword
keyword_counts = Counter(keywords)

# Write the results to a new CSV file
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Count', 'Keyword'])  # Write the header row
    for keyword, count in keyword_counts.items():
        writer.writerow([count, keyword])