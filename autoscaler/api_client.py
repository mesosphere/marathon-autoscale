import os
import requests
import json
import jwt
import sys
import logging
import time


class APIClient:

    DCOS_CA = 'dcos-ca.crt'
    ERR_THRESHOLD = 10

    def __init__(self, dcos_master):
        self.dcos_master = dcos_master
        self.dcos_headers = {}
        self.authenticate()
        self.log = logging.getLogger("autoscaler")

    def authenticate(self):
        """Using a userid/pass or a service account secret,
        get or renew JWT auth token
        Returns:
            Sets dcos_headers to be used for authentication
        """

        # Get the cert authority
        if not os.path.isfile(self.DCOS_CA):

            response = requests.get(
                self.dcos_master + '/ca/dcos-ca.crt',
                verify=False
            )
            with open(self.DCOS_CA, "wb") as crt_file:
                crt_file.write(response.content)

        # Authenticate using using username and password
        if ('AS_USERID' in os.environ.keys()) and ('AS_PASSWORD' in os.environ.keys()):

            auth_data = json.dumps(
                {
                    'uid': os.environ.get('AS_USERID'),
                    'password': os.environ.get('AS_PASSWORD')
                }
            )

        # Authenticate using a service account
        elif ('AS_SECRET' in os.environ.keys()) and ('AS_USERID' in os.environ.keys()):

            # Get the private key from the auto-scaler secret
            saas = json.loads(os.environ.get('AS_SECRET'))

            # Create a JWT token
            jwt_token = jwt.encode(
                {'uid': os.environ.get('AS_USERID')}, saas['private_key'], algorithm='RS256'
            )
            auth_data = json.dumps(
                {
                    "uid": os.environ.get('AS_USERID'),
                    "token": jwt_token.decode('utf-8')
                }
            )

        # No authentication
        else:
            self.dcos_headers = {'Content-type': 'application/json'}
            return

        # Create or renew auth token for the service account
        response = requests.post(
            self.dcos_master + "/acs/api/v1/auth/login",
            headers={"Content-type": "application/json"},
            data=auth_data,
            verify=self.DCOS_CA
        )

        result = response.json()

        if 'token' not in result:
            sys.stderr.write("Unable to authenticate or renew JWT token: %s", result)
            sys.exit(1)

        self.dcos_headers = {
            'Authorization': 'token=' + result['token'],
            'Content-type': 'application/json'
        }

    def dcos_rest(self, method, path, data=None):
        """Common querying procedure that handles 401 errors
        Args:
            method (str): HTTP method (get or put)
            path (str): URI path after the mesos master address
        Returns:
            JSON requests.response.content result of the query
        """
        err_num = 0
        done = False

        while not done:
            try:
                if data is None:
                    response = requests.request(
                        method,
                        self.dcos_master + path,
                        headers=self.dcos_headers,
                        verify=False
                    )
                else:
                    response = requests.request(
                        method,
                        self.dcos_master + path,
                        headers=self.dcos_headers,
                        data=data,
                        verify=False
                    )

                self.log.debug("%s %s %s", method, path, response.status_code)
                done = True

                if response.status_code != 200:
                    if response.status_code == 401:
                        self.log.info("Token expired. Re-authenticating to DC/OS")
                        self.authenticate()
                        done = False
                        continue
                    else:
                        response.raise_for_status()

                content = response.content.strip()
                if not content:
                    content = "{}"

                result = json.loads(content)

                return result

            except requests.exceptions.HTTPError as http_err:
                done = False
                self.log.error("HTTP Error: %s", http_err)
            except json.JSONDecodeError as dec_err:
                done = False
                err_num += 1
                time.sleep(10)
                self.log.error("Non JSON result returned: %s", dec_err)
                if err_num > self.ERR_THRESHOLD:
                    self.log.error("FATAL: Threshold of JSON parsing errors "
                                   "exceeded. Shutting down.")
                    sys.exit(1)
