import requests, json, GeodesignHub, config, geojson
from pick import pick
from geojson import FeatureCollection
# A sample script to take a diagram from Geodesign Hub, buffer it and send
# it back as a new diagram using the API.
#
import requests, json, math

import os
import time
import logging
import logging.handlers

class ScriptLogger():
    def __init__(self):
        self.log_file_name = 'logs/latest.log'
        self.path = os.getcwd()
        self.logpath = os.path.join(self.path, 'logs')
        if not os.path.exists(self.logpath):
            os.mkdir(self.logpath)
        self.logging_level = logging.INFO
        # set TimedRotatingFileHandler for root
        self.formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
        # use very short interval for this example, typical 'when' would be 'midnight' and no explicit interval
        self.handler = logging.handlers.TimedRotatingFileHandler(self.log_file_name, when="S", interval=30, backupCount=10)
        self.handler.setFormatter(self.formatter)
        self.logger = logging.getLogger() # or pass string to give it a name
        self.logger.addHandler(self.handler)
        self.logger.setLevel(self.logging_level)
    def getLogger(self):
        return self.logger




if __name__ == "__main__":
	
	myAPIHelper = GeodesignHub.GeodesignHubClient(url = config.apisettings['serviceurl'], project_id=config.apisettings['projectid'], token=config.apisettings['apitoken'])
	counter =0

	myLogger = ScriptLogger()
	logger = myLogger.getLogger()
	session = requests.Session()
	logger.info("Starting job")

	def get_jobs(page =0):
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
	logger.info("Downloaded %s responses from survey" % len(downloaded_data_results))
	# with open('downloaded_data.json','w') as ipfile:
	# 	ipfile.write(json.dumps(downloaded_data_results))
	submissions_to_upload = []

	logger.info("Downloading project systems")
	systems_response = myAPIHelper.get_all_systems()
	system_list = []
	system_options = []
	counter = 0
	if systems_response.status_code == 200:
		systems_response_json = json.loads(systems_response.text)
		for system in systems_response_json: 
			system_list.append({'system_id':system['id'], 'system_name':system['sysname'], 'counter':counter})
			system_options.append(system['sysname'])
			counter+= 1
	else:
		logger.error("Error in downloading systems: %s" % systems_response.text)

	funding_type_dict = {'budgeted':'b','public':'pu', 'private':'pr', 'public-private':'pp', 'other':'o','unknown':'u'}

	project_or_policy_options = ['project', 'policy', 'DO NOT ADD']

	funding_type_options = ['budgeted', 'public', 'private', 'public-private','other', 'unknown']

	for current_result in downloaded_data_results:				
		project_or_policy_or_skip, project_or_policy_or_skip_index = pick(project_or_policy_options, 'Title: ' + current_result['comment']+ '\nCategory:' + current_result['category'])
				
		if project_or_policy_or_skip_index != 2:
			funding_type, funding_type_index = pick(funding_type_options, 'Title: ' + current_result['comment']+ '\nCategory:' + current_result['category'])
			funding_type = funding_type_dict[funding_type]
			
			selected_system_option, selected_system_index = pick(system_options, 'Title: ' + current_result['comment'] + '\nCategory: ' + current_result['category'])
			system_list_filtered = list(filter(lambda x: x['counter'] == selected_system_index, system_list))
			selected_system_id = system_list_filtered[0]['system_id']
			diagram_description = current_result['comment']

			if diagram_description is not None:
				diagram_description = (diagram_description[:50] + '..') if len(diagram_description) > 50 else diagram_description
			else: 
				diagram_description = 'Externally added Diagram.'

			feature = geojson.loads(json.dumps(current_result['geojson']))
			fc = FeatureCollection([feature])
			fc_to_upload = json.loads(geojson.dumps(fc))
			submissions_to_upload.append({"projectorpolicy":project_or_policy_or_skip, "featuretype":"polygon", "description":diagram_description, "sysid":selected_system_id, "geojson":fc_to_upload, "funding_type":funding_type})

	for current_submission_to_upload in submissions_to_upload:
		if config.apisettings['dryrun']:
			print(current_submission_to_upload)
		else:
			try:
				upload = myAPIHelper.post_as_diagram(geoms = current_submission_to_upload['geojson'], projectorpolicy= current_submission_to_upload['projectorpolicy'],featuretype = current_submission_to_upload['featuretype'], description= current_submission_to_upload['description'], sysid = current_submission_to_upload['sysid'], fundingtype = current_submission_to_upload["funding_type"])
			except Exception as e: 
				print("Error in upload :" % e)
				logging.error("Error in upload %s" % e)
			else:
				print(upload.json())
				
			
