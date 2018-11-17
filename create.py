import sqlite3
from faker import Faker
import random
import os
import http.client, urllib.request, urllib.parse, urllib.error, base64
import uuid
import json
import urllib
import requests
import csv
from urllib import request as urlrequest 




db = sqlite3.connect('database1.db')
cursor = db.cursor()
#cursor.execute("CREATE TABLE refugees (id integer PRIMARY KEY, fullname text, picturepath text UNIQUE, age integer, gender text, nationality text, azure_response text)")

#for i in range(1,5566):
#	name = fake.name().split(' ')
#	addr = fake.address().split('\n')
#	trafficked = random.randint(0,1)
#	cursor.execute("""
#	INSERT INTO refugees (first_name, last_name, nickname, last_seen, picturepath, trafficked) VALUES ("{}", "{}", "{}", "{}", "{:07d}", "{}") 
#	""".format(name[-2],name[-1],name[0],addr[-1],i,trafficked))
#print(l1)	

"""
list = open('interpol_pics.txt', 'r')

print(list.readline())

"""





def enroll_user(url, fullname, nationality, age):

    print(fullname + ' ' + str(age) + ' ' + nationality)

    opener=urlrequest.build_opener()
    opener.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
    urlrequest.install_opener(opener)

    filename = uuid.uuid4().hex + '.jpg'

    urlrequest.urlretrieve(url, os.path.join('/home/vinculum/server-side/vinculum/static/reuploads/', filename))


    headers = {'Content-Type': 'application/json',
               'Ocp-Apim-Subscription-Key': ''} #IMPORT FROM CONFIG FILE
    params = urllib.parse.urlencode({})
    # Create Person
    conn = http.client.HTTPSConnection('southcentralus.api.cognitive.microsoft.com')
    body = "{'name': '%s', 'userData': '%s'}" % (fullname, url)
    conn.request("POST", "/face/v1.0/largepersongroups/2/persons?%s" % params, body, headers)
    response = conn.getresponse()
    data = response.read()
    print(data)
    person_id = eval(data)['personId']
    print(person_id)
    
    # Add Face
    body = "{'url': '%s'}" % url
    conn.request("POST", "/face/v1.0/largepersongroups/2/persons/%s/persistedfaces?%s" % (person_id, params), body, headers)
    response = conn.getresponse()
    data = response.read()
    print(data)

    # Re-train
    #conn.request("POST", "/face/v1.0/largepersongroups/2/train?%s" % params, "{}", headers)
    #response = conn.getresponse()
    #data = response.read()
    #conn.close()
    #print(data)

    db = sqlite3.connect('database1.db')
    cursor = db.cursor()

    output = cursor.fetchall()
    #cursor.execute("""UPDATE refugees SET azure_response={} WHERE picturepath={}""")
    cursor.execute("""INSERT INTO refugees (fullname, picturepath, age,  nationality, azure_response, uploader_name, source) values ('{}', '{}', {}, '{}', '{}', 'INTERPOL', 'INTERPOL')""".format(fullname, filename, age, nationality, person_id))

    db.commit()
    db.close()



    return 'success' 

count = 0

"""
for line in open('interpol_pics.txt', 'r'):
    count += 1
    if count == 5:
        enroll_user(line)
        print(count)
"""

with open('interpol_pics_descriptors.txt', 'r') as csvfile:
    for row in csvfile:
        if count > 3:
            line = row.split(';')
            
        
            print(line)
            enroll_user(line[-1].strip(),line[0],line[2], line[1].strip())
        count += 1


cursor.execute("SELECT count(*) FROM refugees")
print(cursor.fetchall())
