# CREATE A PERSON
import http.client, urllib.request, urllib.parse, urllib.error, base64
subscription_key = "#########"
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
    
    body = "{'faceIds': ['%s'], 'largePersonGroupId': '1'}" % face_id
    print(body)
    
    try:
        conn = http.client.HTTPSConnection('westeurope.api.cognitive.microsoft.com')
        conn.request("POST", "/face/v1.0/identify?%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        personId = eval(data)[0]['candidates'][0]['personId']
        print(data)
        conn.close()
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
    
    
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
        return data
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
