import os
import os.path
import json
from flask import Flask
from flask import request
from flask import Response
from flask import render_template
import time
import boto3

app = Flask(__name__)
alert_folder = './'
client = boto3.client('s3')
#the s3 bucket name is declared by the service wrapper 
bucket_name = str(os.environ.get('S3_BUCKET_NAME'))

def key_exists(mykey, mybucket=bucket_name):
    try:
        client.head_object(Bucket=mybucket, Key=mykey)
        return True
    except Exception as e:
        print(e)
        return False

@app.route("/healthcheck", methods=['GET'])
def heartbeat():
    return "OK", 200

@app.route("/alert-listener", methods=['POST'])
def alert_listener():
    #setup s3 object

    ts = time.time()
    if 'Content-Type' in request.headers and request.headers['Content-Type'] == 'application/json':
        alert = request.json
    else:
        try:
            alert = json.loads(request.data)
        except Exception as e:
            return e, 500

    #check if this update is a resolution event
    if alert['alert_action'] == 'resolve':
        alert['name'] = alert['name'].replace('[RESOLVED] ', '')

    alert['last_update_ts'] = ts
    # using team name if found
    team_name = ''
    team_name_list = [obj for obj in alert['fields'] if 'key' in obj and obj['key'] == 'team']
    if len(team_name_list) > 0 and 'value' in team_name_list[0]:
        team_name = team_name_list[0]['value']
    s3_path = team_name + str(alert['name']).replace(' ','_').lower() + '.status'  
    if not key_exists(s3_path):
        alert['alert_first_report'] = ts
    else:
        #load original file from s3
        obj = client.get_object(Bucket=bucket_name, Key=s3_path)
        old_alert_json = json.loads(obj['Body'].read())
        alert['alert_first_report'] = old_alert_json['alert_first_report']

    #write new mutex file
    client.put_object(
        Body=json.dumps(alert), 
        Bucket=bucket_name, 
        Key=s3_path
        )
    #debug input of errors
    # print(json.dumps(alert, indent=2))
    return "Alert status updated", 200

'''
HTTP 201 is alert triggered
HTTP 202 is alert resolved
'''

@app.route("/check-alert-status", methods=['GET'])
def check_status():
    alert_name = request.args.get('alert_name')
    team_name = ''
    team_name_list = [obj for obj in alert['fields'] if 'key' in obj and obj['key'] == 'team']
    if len(team_name_list) > 0 and 'value' in team_name_list[0]:
        team_name = team_name_list[0]['value']
    s3_path = team_name + str(alert['name']).replace(' ','_').lower() + '.status'
    print(s3_path)

    try:
        if key_exists(s3_path):
            obj = client.get_object(Bucket=bucket_name, Key=s3_path)
            alert_json = json.loads(obj['Body'].read())
            print(json.dumps(alert_json, indent=2))
            if alert_json['alert_action'] == 'trigger':
                return json.dumps(alert_json, indent=2, sort_keys=True), 201

            if alert_json['alert_action'] == 'resolve':
                return json.dumps(alert_json, indent=2, sort_keys=True), 202

        else:
            return "Alert not found or never triggered", 404

    except Exception as e:
        return "Alert not found or never triggered", 404

@app.route("/", methods=['GET'])
def render_alert_list():
    #list of current triggered
    info_list = []
    for file in client.list_objects(Bucket=bucket_name)['Contents']:
        print(file['Key'])
        
        obj = client.get_object(Bucket=bucket_name, Key=file['Key'])
        alert_json = json.loads(obj['Body'].read())
        info_list.append({ "name" : alert_json['name'], "status" : alert_json['alert_action']})
    print (info_list)
    rendered = render_template('index.html', \
        title = "Current Alerts", \
        alerts = info_list)

    return rendered, 200

@app.route("/only_triggered_alerts", methods=['GET'])
def list_triggered_alerts():
    #list of current triggered alerts
    result_json = {
        "triggered_item_count" : 0 ,
        "resolved_item_count" : 0 ,
        "triggered_alerts_list" : []
    }
    for file in client.list_objects(Bucket=bucket_name)['Contents']:
        print(file['Key'])
        
        obj = client.get_object(Bucket=bucket_name, Key=file['Key'])
        alert_json = json.loads(obj['Body'].read())
        if alert_json['alert_action'] == 'trigger':
            result_json['triggered_alerts_list'].append(alert_json)
            result_json['triggered_item_count'] += 1
        if alert_json['alert_action'] == 'resolve':
            result_json['resolved_item_count'] += 1

    return json.dumps(result_json, indent=2, sort_keys=True), 200
 
@app.route("/resolve_alert", methods=['POST'])
def reset_alert_status(ts = time.time()):
    #get the alert name to reset, either a specific name or all
    alert_to_reset = request.args.get('alert_name').lower()

    #reset one alert or all with 'all' or 'name' arguments
    if alert_to_reset == 'all':
        for file in client.list_objects(Bucket=bucket_name)['Contents']:
            print(file['Key'])

            obj = client.get_object(Bucket=bucket_name, Key=file['Key'])
            alert_json = json.loads(obj['Body'].read())
            
            if alert_json['alert_action'] == 'trigger':
                alert_json['alert_action'] = 'resolve'
                alert_json['last_update_ts'] = ts
                
                #write new mutex file
                client.put_object(
                    Body=json.dumps(alert_json), 
                    Bucket=bucket_name, 
                    Key=file['Key']
                    )
        return "All triggered alerts were reset", 200
    else:
        team_name = ''
        team_name_list = [obj for obj in alert['fields'] if 'key' in obj and obj['key'] == 'team']
        if len(team_name_list) > 0 and 'value' in team_name_list[0]:
            team_name = team_name_list[0]['value']
        s3_path = team_name + str(alert['name']).replace(' ','_').lower() + '.status'
        obj = client.get_object(Bucket=bucket_name, Key=s3_path)
        alert_json = json.loads(obj['Body'].read())
        if alert_json['alert_action'] == 'trigger':
            alert_json['alert_action'] = 'resolve'
            alert_json['last_update_ts'] = ts
            
            #write new mutex file
            client.put_object(
                Body=json.dumps(alert_json), 
                Bucket=bucket_name, 
                Key=s3_path
                )
            return "Triggered alert were reset", 200
        else:
            return "Specified alerts is not in trigger state", 200

    return "Alert status updated", 200
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    #
    print("app will run on port: {}".format(port))
    print("state s3 bucket: {}".format(bucket_name))
    app.run(host='0.0.0.0', port=port)