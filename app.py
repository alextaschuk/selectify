from flask import Flask, render_template, redirect, request, session
import requests
from dotenv import load_dotenv
import os
import random
import math
import base64

app = Flask(__name__)

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")
app.secret_key = os.getenv("SECRET_KEY")

scope = 'user-library-read'

def generateRandomString(length):
    text = ''
    possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    for x in range(length):
        text += possible[math.floor(random.randint(0, len(possible) - 1))]
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    state = generateRandomString(16)
    session['stored_state'] = state
    return redirect('https://accounts.spotify.com/authorize?response_type=code&client_id=' + str(client_id) + '&scope=' + str(scope) + '&redirect_uri=' + str(redirect_uri) + '&state=' + str(state))

@app.route('/callback', methods=['GET', 'POST'])
def callback():
    auth_code = request.args.get('code', None)
    state = request.args.get('state', None)
    stored_state = session.get('stored_state')

    if state == None or state != stored_state:
        print('Didnt work')
        return render_template('index.html')
    else:
        credentials = f"{client_id}:{client_secret}"
        base64_credentials = base64.b64encode(
            credentials.encode("utf-8")).decode("utf-8")
        url = 'https://accounts.spotify.com/api/token'
        data = {
            'code': auth_code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        headers = {
            'Authorization': f'Basic {base64_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        get_access_token = requests.post(url, data=data, headers=headers)

        if get_access_token.status_code == 200:
            access_token_data = get_access_token.json()
            access_token = access_token_data['access_token']
            scope = access_token_data['scope']
            refresh_token = access_token_data['refresh_token']

            def get_album_names(album_info):
                for item in album_info['items']:
                    album = item['album']
                    album_names.append(album['name'])

            url = 'https://api.spotify.com/v1/me/albums?limit=25'
            headers = {
                'Authorization': 'Bearer ' + str(access_token)
            }
            api_data = requests.get(url, headers=headers)

            album_info = api_data.json()
            album_names = []
            get_album_names(album_info)

            while album_info['next']:
                url = album_info['next']
                api_data = requests.get(url, headers=headers)
                album_info = api_data.json()
                get_album_names(album_info)

            for x in range(3):  # shuffle list of album names 3 times for extra randomization
                random.shuffle(album_names)

            list_index = random.randrange(
                len(album_names) - 1)  # get random index value
            album_to_listen_to = album_names[list_index]  # get album

            return album_to_listen_to + ' was chosen.'

        else:
            return 'error'

@app.route('/refresh_token')
def refresh_token():
    credentials = f"{client_id}:{client_secret}"
    base64_credentials = base64.b64encode(
        credentials.encode("utf-8")).decode("utf-8")
    url = 'https://api.spotify.com/v1/me/albums'
    refresh_token = response_data['refresh_token']

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    headers = {
        'Authorization': f'Basic {base64_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    refresh = requests.post(url, data=data, headers=headers)
    if refresh.status_code == 200:
        response_data = refresh.json()
        new_access_token = response_data['access_token']
        token_type = response_data['token_type']
        scope = response_data['scope']
        expires_in = response_data['expires_in']
        return 'New Access Token: ' + str(new_access_token)
    else:
        return 'Could not generate new access token.'

if __name__ == '__main__':
    app.run(host='192.168.4.92', port=80)