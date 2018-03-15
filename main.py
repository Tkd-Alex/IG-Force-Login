from bot import Bot
from flask import Flask, request, Response
from datetime import datetime
from pprint import pprint
import json, pickle, os, time

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    _data = request.get_json()
    proxy_address             = _data['proxy_address']              if 'proxy_address' in _data else "" 
    proxy_port                = _data['proxy_port']                 if 'proxy_port' in _data else 0
    bypass_suspicious_attempt = _data['bypass_suspicious_attempt']  if 'bypass_suspicious_attempt' in _data else False
    verify_code_mail          = _data['verify_code_mail']           if 'verify_code_mail' in _data else False
    session = Bot(
        username=_data['username'],
        password=_data['password'],
        proxy_address=proxy_address,
        proxy_port=int(proxy_port),
        bypass_suspicious_attempt=bypass_suspicious_attempt,
        verify_code_mail=verify_code_mail,
        nogui=True,
        headless_browser=True
    )
    status, message = session.login()
    js = json.dumps({ 'result': status, 'message': message })
    session.end()
    if status:
        return Response(js, status=200, mimetype='application/json')
    else:
        return Response(js, status=400, mimetype='application/json')

@app.route('/code', methods=['POST'])
def code():
    _data = request.get_json()
    proxy_address              = _data['proxy_address']              if 'proxy_address' in _data else ""
    proxy_port                 = _data['proxy_port']                 if 'proxy_port' in _data else 0
    bypass_suspicious_attempt  = _data['bypass_suspicious_attempt']  if 'bypass_suspicious_attempt' in _data else False
    verify_code_mail           = _data['verify_code_mail']           if 'verify_code_mail' in _data else False
    session = Bot(
        username=_data['username'],
        password=_data['password'],
        proxy_address=proxy_address,
        proxy_port=int(proxy_port),
        bypass_suspicious_attempt=bypass_suspicious_attempt,
        verify_code_mail=verify_code_mail,
        nogui=True,
        headless_browser=True
    )
    status, message = session.code(_data['code'])
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
    app.run(host='0.0.0.0', port=4587, threaded=True, debug=True)
