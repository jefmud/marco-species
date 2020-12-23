# create_study_collection.py
# a program to create a "reduced" study collection
# over a particular date interval
# the reduced collection is MUCH faster to query
# than the entire identifications collection

import pymongo

# handle mongo configuration local/protected
mongo_uri = 'mongodb://127.0.0.1:27017'
dbname = 'ser'
new_collection = 'study_2018_reduced'
idents_collection = 'idents'

# make sure privileged user types in
resp = input("This program DROPS the {} collection.  Are you sure? Type I AGREE\n".format(new_collection))
if resp != "I AGREE":
    import sys
    # exit to OS
    print("Exiting to OS")
    sys.exit(0)

import datetime
# start of period 2018-04-15
start_datetime = datetime.datetime(2018,4,15)
# end of period, 2018-09-01 (not inclusive)
end_datetime = datetime.datetime(2018,9,1)
# temporary test of two days of data
#end_datetime = datetime.datetime(2018,4,17)

# delta is number of days in a query window
# practically speaking in the low memory space, I found 7 days to be servicable
delta = 7

def sdate(d):
    """ sdate(d) - string date from datetime
    :param d: input datetime object
    returns a string of date ONLY
    format: YYYY-MM-DD
    """
    if not isinstance(d, datetime.datetime):
        raise ValueError("sdate(d) - d must be a datetime object")
    return str(d).split(' ')[0]

# try to connect to Mongo URI
client = pymongo.MongoClient(mongo_uri)

# connect to specific database in dbname
db = client[dbname]

# drop the new_collection before building it.
db.drop_collection(new_collection)

# current is the loop's current date, and end date will be current + delta (days)
current = start_datetime

# loop sentinal "done"
done = False
while not done:
    # convert start_date, end_date as strings of YYYY-MM-DD
    start_date = sdate(current)
    end_date = sdate(current + datetime.timedelta(delta))
    # if end_date EXCEEDS study end_datetime,
    # change end_date to match end_datetime and set "done" sentinal
    if end_date > sdate(end_datetime):
        end_date = sdate(end_datetime)
        done = True
    # show user console what we are going to query
    print("querying {} ==> {}".format(start_date, end_date))
    # perform the query, query between captureDATE
    # second dictionary tells us to EXCLUDE mwePREDS, mwsPREDS,
    # and the object id (this data just slows us down)
    query_response = db[idents_collection].find(
        {'captureDATE':{'$gte':start_date, '$lt':end_date}},
        {'mwePREDS':0, 'mwsPREDS':0, 'mwsCOUNTPREDS':0, '_id':0}
    )
    # tell user how many captureIDs are in the current query
    print(query_response.count())

    # show user we are now inserting data, and when we are done.
    print("inserting")
    db[new_collection].insert_many(query_response)
    print("insert done")

    # advance the current date by delta (days)
    current = current + datetime.timedelta(delta)

# show user we completed writing out the collection
print("****** done ********")
