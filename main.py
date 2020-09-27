import requests
import lxml.html
import time
import os

USERNAME = os.environ['NOIP_USERNAME']
PASSWORD = os.environ['NOIP_PASSWORD']
LOGIN_URL = "https://www.noip.com/login"
URL = "https://my.noip.com/api/host"
UPDATE_INTERVAL=5

def renewAllDomains():
    session = requests.session()
    print("Fetching Login Page...")
    tree = lxml.html.fromstring(session.get(LOGIN_URL).text)
    
    loginPayload = {
        "username": USERNAME,
        "password": PASSWORD,
        "submit_login_page": "1",
        "_token": list(set(tree.xpath("/html/body/section[1]/section/div/div/div/div[1]/div/div[2]/form/input[5]")))[0].value,
    }

    print("Logging in...")
    result = session.post(LOGIN_URL, data = loginPayload)
    if result.status_code != 200:
        print("Failed to Log in.")
        return 1
    headerPayload = {"X-CSRF-TOKEN": result.cookies['XSRF-TOKEN'], "X-Requested-With": "XMLHttpRequest"}
    
    print("Fetching domain information...")
    result = session.get(URL, headers = headerPayload)
    if result.status_code != 200:
        print("Failed to fetch domain information. We may have hit the rate limiter.")
        return 1
    try:
        expiringDomains = False
        for domain in result.json()['hosts']:
            print("Found domain: " + domain['hostname'] + ", expiring in " + str(domain['days_remaining']) + " days")
            if domain['is_expiring_soon']:
                print("... and it's expiring!")
                expiringDomains = True
                session.get(URL + "/" + str(domain['id']) + "/touch", headers = headerPayload)
        
        if expiringDomains:
            print("Found expired domains. Making sure that is no longer the case.")
            if result.status_code != 200:
                print("Failed to fetch domain information. We may have hit the rate limiter.")
                return 1
            result = session.get(URL, headers = headerPayload)
            for domain in result.json()['hosts']:
                print("Found domain: " + domain['hostname'])
                if domain['is_expiring_soon']:
                    print("... and it's expiring!")
                    raise ValueError("Some hosts are still set to expire despite attempting to update them!")
        print("Done.")
        return 0
    except (ValueError, JSONDecodeError) as e:
        print ("Failed to update: " + e)
        print (result.text)
        return 1

if __name__ == "__main__":
    while True:
        renewAllDomains()
        time.sleep(UPDATE_INTERVAL * 3600)
        
