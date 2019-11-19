import json
import logging
import logging.handlers
import os
import urllib
import random
import secrets
import string 
import sys
import itsdangerous
import requests
from dotenv import load_dotenv
import flask
from flask import Flask, request, Response

load_dotenv()
app = Flask(__name__)

# Configure logging
LOGGER = logging.getLogger()
log_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.handlers.RotatingFileHandler(filename=os.environ['LOG_FILENAME'],
                                                    mode="a+",
                                                    maxBytes=50 * 1024 * 1024, # 50 MiB
                                                    backupCount=2,
                                                    encoding=None, delay=False)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(file_handler)
LOGGER.info("GitHub Replicator app started")

AUTHORIZE_URI = "https://github.com/login/oauth/authorize"
ACCESS_TOKEN_URI = "https://github.com/login/oauth/access_token"
API_URI = "https://api.github.com"
SOURCE_REPO = "lkingsford/github_replicator"

@app.route('/')
def root():
    """Root that is called at / or index. This is generally the first page that
    a user will go to, and redirects them to sign in to GitHub"""
    redirect_params = {
        'client_id': os.environ['GITHUB_CLIENT_ID'],
        'redirect_uri': 'https://{host}/github_callback'.format(host=os.environ['HOST']),
        'scope': 'public_repo',
        'state': generate_state()
    }
    LOGGER.info("Sending redirect")
    LOGGER.debug("Using %s", redirect_params)
    params = urllib.parse.urlencode(redirect_params)
    redirect_uri = "{}?{}".format(AUTHORIZE_URI, params)
    LOGGER.debug("Redirect URI is %s", redirect_uri)
    return flask.redirect(redirect_uri)

@app.route('/github_callback')
def github_callback():
    """Route that is called by github, and gets an access token"""
    logging.info("Received Callback")
    logging.debug("Args: %s", request.args)
    # OAuth authorizes, and then redirects with a param with a code
    # that can be exchanged for an access token
    code = request.args.get('code')
    state = request.args.get('state')
    if not verify_state(state):
        return Response('State does not match - potential cross-site forgery',
                        401)
    authorize_params = {
        'client_id': os.environ['GITHUB_CLIENT_ID'],
        'client_secret': os.environ['GITHUB_CLIENT_SECRET'],
        'code': code
    }
    params = urllib.parse.urlencode(authorize_params)
    access_post_uri = "{}?{}".format(ACCESS_TOKEN_URI, params)
    logging.debug("Requesting token with '%s'", access_post_uri)
    response = requests.post(access_post_uri)
    # Response is in the form of 'access_token=<Access Token>&token_type=bearer
    # where <Access Token> is the actual token to use
    token_raw = response.content.decode('utf-8')
    logging.debug("Response was %s", token_raw)
    token = token_raw[token_raw.find('=') + 1 : token_raw.find('&')]
    logging.debug("Token is %s", token)

    # Duplicate repository
    # We're going to fork, so future users can get changes
    auth_headers = {"Authorization":"token {}".format(token)}
    logging.debug("Authorizing with %s", auth_headers)
    response = requests.post("{}/repos/{}/forks".format(API_URI, SOURCE_REPO),
                             headers=auth_headers)
    if response.status_code == 202:
        logging.info("Forked repo successfully. Response was %s",
            response.content.decode("utf-8"))
        # The repo is forked successfully. Redirect to it.
        json_response = json.loads(response.content)
        url = json_response["html_url"]
        return flask.redirect(url)
    else:
        logging.error("Failed to fork repo. Response was %s",
            response.content.decode("utf-8"))
        return "Failed to fork repo. Full response has been logged."

def generate_state():
    """Generate a state to pass to GitHub
    
    Normally, this might use a DB and store the actual state - but we're doing
    an encryption style state instead, so we don't have to keep additional
    infrastructure.
    
    We generate a random 12 character string, and then sign it with the
    state_key using itsdangerous. We use the same key to validate with
    itsdangerous the other way.
    """
    signer = itsdangerous.Signer(os.environ['STATE_KEY'])
    # Using secrets, as Python's doco makes clear that random is not suitable
    # for anything remotely security
    allowed_characters = string.ascii_letters + string.digits
    to_sign = ''.join([secrets.choice(allowed_characters) for i in range(12)])
    return signer.sign(to_sign).decode('utf-8')

def verify_state(state):
    """Verify the state GitHub returned is valid

    See `generate_state` for how this is verified
    """
    signer = itsdangerous.Signer(os.environ['STATE_KEY'])
    return signer.validate(state)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
