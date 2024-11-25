import json
import config
import requests

import math
from pathlib import Path
import re

if __name__ == "__main__":

    session = requests.Session()

    token = config.apisettings['apitoken']
    token_string = 'Token {auth_token}'.format(auth_token = token)
    headers = {
        'Authorization': token_string
    }

    session.headers = headers


    def get_jobs(page=0):
        url = config.apisettings['job_url']
        first_page = session.get(url).json()
        yield first_page
        count = math.ceil(first_page['count']/10)

        for page in range(2, count + 1):
            next_page = session.get(url,params={'page': page}).json()
            yield next_page

    downloaded_data_results = []

    for page in get_jobs():
        downloaded_data_results += page['results']

    print("Downloaded %s responses from survey" % len(downloaded_data_results))
       
    Path("downloaded_data/geojson").mkdir(parents=True, exist_ok=True)

    for current_row in downloaded_data_results:        
        filename = current_row['comment'][:20]
        filename = re.sub('\W+',' ', filename )
        with open('downloaded_data/geojson/' + filename + '.geojson', mode='w') as geojson_output:
            geojson_output.write(json.dumps(current_row['geojson']))
