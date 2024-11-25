import config
import requests
import csv
import math
from pathlib import Path

if __name__ == "__main__":

    session = requests.Session()

    token = config.apisettings['apitoken']
    token_string = 'Token {auth_token}'.format(auth_token = token)
    headers = {
        'Authorization': token_string
    }

    def get_jobs(page=0):
        url = config.apisettings['comments_url']
        first_page = session.get(url ,headers= headers).json()
        yield first_page
        count = math.ceil(first_page['count']/10)

        for page in range(2, count + 1):
            next_page = session.get(url,  headers= headers,params={'page': page}).json()
            yield next_page

    downloaded_data_results = []

    for page in get_jobs():
        downloaded_data_results += page['results']

    print("Downloaded %s responses from survey" % len(downloaded_data_results))
    
    Path("downloaded_data").mkdir(parents=True, exist_ok=True)
    with open('downloaded_data/survey_comments.csv', mode='w') as survey_results:
        survey_results_writer = csv.writer(survey_results, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        survey_results_writer.writerow(['id','Date-Time created', 'Comment Text','Survey Response ID'])
        for current_row in downloaded_data_results:
            survey_results_writer.writerow([current_row['id'],current_row['created_at'], current_row['comment_text'],current_row['survey_response']])
