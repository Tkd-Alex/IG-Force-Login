from bot import Bot
from flask import Flask, request, Response
from datetime import datetime
from pprint import pprint
import json, pickle, os, time, random

app = Flask(__name__)

def parse_params(params):
    data = params
    data['proxy_address']             = params['proxy_address']              if 'proxy_address' in params else "" 
    data['proxy_port']                = params['proxy_port']                 if 'proxy_port' in params else 0
    data['bypass_suspicious_attempt'] = params['bypass_suspicious_attempt']  if 'bypass_suspicious_attempt' in params else False
    data['verify_code_mail']          = params['verify_code_mail']           if 'verify_code_mail' in params else False
    data['use_vpn']                   = params['use_vpn']                    if 'use_vpn' in params else False

    return data

def init_bot(params):
    return Bot(
        username = params['username'],
        password = params['password'],
        proxy_address = params['proxy_address'],
        proxy_port = int(params['proxy_port']),
        bypass_suspicious_attempt = params['bypass_suspicious_attempt'],
        verify_code_mail = params['verify_code_mail'],
        use_vpn = params['use_vpn'],
        nogui = True,
        page_delay = 10
    )

@app.route('/delete', methods=['POST'])
def delete():
    data = parse_params(request.get_json())
    username = data['username']
    try:
        if os.path.isfile('cookies/{}_cookie.pkl'.format(username)):
            os.remove('cookies/{}_cookie.pkl'.format(username))
        if os.path.isfile('sessions/{}_session.pkl'.format(username)):
            os.remove('sessions/{}_session.pkl'.format(username))
        js = json.dumps({ 'result': True, 'message': "{} deleted".format(username) })
        return Response(js, status=200, mimetype='application/json')
    except Exception as e:
        print("[Error]\t{}".format(e))
        js = json.dumps({ 'result': False, 'message': "{} deleted fail".format(username) })
        return Response(js, status=400, mimetype='application/json')

@app.route('/login', methods=['POST'])
def login():
    data = parse_params(request.get_json())
    session = init_bot(data)
    status, message = session.login()
    js = json.dumps({ 'result': status, 'message': message })
    session.end()
    if status:
        return Response(js, status=200, mimetype='application/json')
    else:
        return Response(js, status=400, mimetype='application/json')

@app.route('/code', methods=['POST'])
def code():
    data = parse_params(request.get_json())
    session = init_bot(data)
    status, message = session.code(data['code'])
    js = json.dumps({ 'result': status, 'message': message })
    session.end()
    if status:
        return Response(js, status=200, mimetype='application/json')
    else:
        return Response(js, status=400, mimetype='application/json')

@app.route('/',  methods=['GET', 'POST'])
def hello():
    message = "Viral-Force-Login Working on: {}".format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
    return Response(message, status=200, mimetype='application/json')

if __name__ == '__main__':
    if not os.path.exists("sessions"):
        os.makedirs("sessions")
    if not os.path.exists("screenshot"):
        os.makedirs("screenshot")    
    app.run(host='0.0.0.0', port=4587, threaded=True, debug=False)
