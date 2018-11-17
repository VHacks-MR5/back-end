from flask import Flask, request, render_template, url_for, jsonify
from werkzeug.utils import secure_filename
import os
import http.client, urllib.request, urllib.parse, urllib.error, base64
import sqlite3
import uuid
import json
UPLOAD_FOLDER = '/home/nyanta/static/uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DATABASE = '/home/nyanta/database.db'



@app.route('/')
def hello_world():
	return 'Hello world!'



@app.route('/find', methods=['GET','POST'])
def find():
	if request.method == 'GET':
		context1 = 'teststring'
		return render_template('test.html', context = context1)

	elif request.method == 'POST':
		context = request.get_json(force=True)
		user = request.files['user']
		userfile = str(uuid.uuid4())
		family = request.files['family']
		familyfile = str(uuid.uuid4())
		db = sqlite3.connect(DATABASE)
		cursor = db.cursor()
		cursor.execute("INSERT INTO refugees (first_name, last_name, picturepath, age, gender, nationality, nickname) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(context['my_name'],context['my_last_name'], userfile,context['my_age'], context['my_sex'], context['my_nationality'], context['my_nickname']))
			
		cursor.execute("INSERT INTO refugees (first_name, last_name, picturepath, age, gender, nationality, nickname) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(context['person_name'],context['person_last_name'], familyfile,context['person_age'], context['person_sex'], context['person_nationality'], context['person_nickname']))

		db.commit()	
		db.close()
		user.save(os.path.join(app.config['UPLOAD_FOLDER'], userfile))
		family.save(os.path.join(app.config['UPLOAD_FOLDER'], familyfile))
		return 'success',200


@app.route('/match', methods=['GET'])
def match():
	url = '/static/uploads/' + request.args.get('token')
	return get_matches(url)	


@app.route('/match/app', methods=['GET'])
def app_match():
	url = request.args.get('url')
	data, confidence = get_matches(url)
	response = str(data)[str(data).find('jpg')-8:str(data).find('jpg')+3]
	url = 'https://familylinks.icrc.org/europe/PersonImages/' + response
	response = {'messages':[{'text': 'Similarity score is %s%%' % int((confidence*100))}, {'attachment':  {"type": "image","payload": {"url": url}}}]}
	#response = {'messages':[ {'text': url} ] }
	return jsonify(response) 



# CREATE A PERSON
subscription_key = "##########"
assert subscription_key

def get_matches(url):
    ##### 1. Convert URL to a faceId
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': subscription_key,
    }
    
    params = urllib.parse.urlencode({
    })
    
    body = "{'url': '%s'}" % url
    try:
        conn = http.client.HTTPSConnection('westeurope.api.cognitive.microsoft.com')
        conn.request("POST", "/face/v1.0/detect?%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        print(data)
        face_id = eval(data)[0]['faceId']
        conn.close()
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
    
    
    
    ##### 2. Get best matching personId from faceId
    params = urllib.parse.urlencode({
    })
    
    body = "{'faceIds': ['%s'], 'largePersonGroupId': '1', 'confidenceThreshold': '0.2'}" % face_id
    print(body)
    
    try:
        conn = http.client.HTTPSConnection('westeurope.api.cognitive.microsoft.com')
        conn.request("POST", "/face/v1.0/identify?%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        personId = eval(data)[0]['candidates'][0]['personId']
        confidence = eval(data)[0]['candidates'][0]['confidence']
        print(data)
        conn.close()
    except Exception as e:
        print("{}".format(str(e)))
    
    
    print(personId)
    
    
    ##### 3. Get name (which is filename) of personId
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': subscription_key,
    }
    
    params = urllib.parse.urlencode({
        'largePersonGroupId': '1',
        'personId': personId,
    })
    
    try:
        conn = http.client.HTTPSConnection('westeurope.api.cognitive.microsoft.com')
        conn.request("GET", "/face/v1.0/largepersongroups/{largePersonGroupId}/persons/{personId}?%s" % params, "{}", headers)
        response = conn.getresponse()
        data = response.read()
        print(data)
        conn.close()
        return data, confidence
    except Exception as e:
        print("[Errno {0}]".format(str(e)))



if __name__ == '__main__':
	app.run(host='IP Address Server is running on')
