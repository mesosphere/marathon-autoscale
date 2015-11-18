__author__ = 'tkraus'
import requests
import json

# marathon_host = 'thomaskra-elasticl-1114imswizjvw-1820440244.us-east-1.elb.amazonaws.com'
marathon_host = input("Enter the resolvable hostname or IP of your Marathon Instance")

marathon_apps=[]

def get_app_ids(marathon_host):
    response=requests.get('http://' + marathon_host+ '/marathon/v2/apps').json()
    if response['apps'] ==[]:
        print 'No Apps Found on Martahon !'
    else:
        for i in response['apps']:
            appid=i['id']
            print appid
            marathon_apps.append(appid)


if __name__ == "__main__":
    get_app_ids(marathon_host)
    print 'Found the following Marathon Apps',marathon_apps
