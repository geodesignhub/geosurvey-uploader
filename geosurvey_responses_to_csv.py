import json
import config
import requests
import csv
import math

if __name__ == "__main__":

    session = requests.Session()

    def get_jobs(page=0):
        url = config.apisettings['job_url']
        first_page = session.get(url).json()
        yield first_page
        count = math.ceil(first_page['count']/10)

        for page in range(2, count + 1):
            next_page = session.get(url, params={'page': page}).json()
            yield next_page

    downloaded_data_results = []

    for page in get_jobs():
        downloaded_data_results += page['results']

    print("Downloaded %s responses from survey" % len(downloaded_data_results))
    
    with open('survey_responses.csv', mode='w') as survey_results:
        survey_results_writer = csv.writer(survey_results, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        survey_results_writer.writerow(['id','Response', 'Category','Upvotes','Downvotes','Comment Count','Open Location Code', 'Date-Time added'])
        for current_row in downloaded_data_results:
            survey_results_writer.writerow([current_row['id'],current_row['comment'], current_row['category'],current_row['upvotes'],current_row['downvotes'],current_row['comment_count'],current_row['open_location_code'], current_row['date_added']])
