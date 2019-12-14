import os
import requests
import json
import jwt
import sys
import logging
import time


class APIClient:

    DCOS_CA = 'dcos-ca.crt'

    def __init__(self, dcos_master):
        self.dcos_master = dcos_master
        self.dcos_headers = {
            'User-Agent': 'marathon-autoscale',
            'Content-type': 'application/json'
        }
        self.authenticate()
        self.log = logging.getLogger("autoscale")

    def authenticate(self):
        """Using a userid/pass or a service account secret,
        get or renew JWT auth token
        Returns:
            Updates dcos_headers to be used for authentication
        """

        # Get the cert authority
        if not os.path.isfile(self.DCOS_CA):

            response = requests.get(
                self.dcos_master + '/ca/dcos-ca.crt',
                headers=self.dcos_headers,
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
            return

        # Create or renew auth token for the service account
        response = requests.post(
            self.dcos_master + "/acs/api/v1/auth/login",
            headers=self.dcos_headers,
            data=auth_data,
            verify=self.DCOS_CA
        )

        result = response.json()

        if 'token' not in result:
            self.log.error("Unable to authenticate or renew JWT token: %s", result)
            sys.exit(1)

        self.dcos_headers.update({
            'Authorization': 'token=' + result['token']
        })

    def dcos_rest(self, method, path, data=None, auth=True):
        """Common querying procedure that handles 401 errors
        Args:
            method (str): HTTP method (get or put)
            path (str): URI path after the mesos master address
        Returns:
            JSON requests.response.content result of the query
        """
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

            if response.status_code != 200:
                if response.status_code == 401 and auth:
                    self.log.info("Token expired. Re-authenticating to DC/OS")
                    self.authenticate()
                    return self.dcos_rest(method, path, data=data, auth=False)
                else:
                    response.raise_for_status()

            content = response.content.strip()
            if not content:
                content = "{}"

            result = json.loads(content)
            return result

        except requests.exceptions.HTTPError as e:
            self.log.error("HTTP Error: %s", e)
            raise
        except Exception as e:
            self.log.error("Error: %s", e)
            raise
