import csv

class WekaCSV(csv.Dialect):
    delimiter = ','
    doublequote = False
    escapechar = '\\'
    lineterminator = '\n'
    quotechar = '"'
    quoting = csv.QUOTE_NONNUMERIC
    skipinitialspace = False
    strict = False