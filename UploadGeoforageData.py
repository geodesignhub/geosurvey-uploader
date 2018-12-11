import requests, json, GeodesignHub, config, geojson
from pick import pick
from geojson import FeatureCollection
# A sample script to take a diagram from Geodesign Hub, buffer it and send
# it back as a new diagram using the API.
#
import requests, json, math

if __name__ == "__main__":
	
	myAPIHelper = GeodesignHub.GeodesignHubClient(url = config.apisettings['serviceurl'], project_id=config.apisettings['projectid'], token=config.apisettings['apitoken'])
	counter =0

	session = requests.Session()


	def get_jobs(page =0):
		url = "https://www.geoforage.io/api/v1/surveys/8e205b3f-e601-4528-b5a7-2a020a17101c/responses/list" 
		first_page = session.get(url).json()
		yield first_page
		count = math.ceil(first_page['count']/10)

		for page in range(2, count + 1):

			next_page = session.get(url, params={'page': page}).json()
			yield next_page


	downloaded_data_results = []
	for page in get_jobs():
			downloaded_data_results += page['results']

	# with open('downloaded_data.json','w') as ipfile:
	# 	ipfile.write(json.dumps(downloaded_data_results))
	submissions_to_upload = []

	systems_response = myAPIHelper.get_systems()
	system_list = []
	system_options = []
	counter = 0
	
	if systems_response.status_code == 200:
		systems_response_json = json.loads(systems_response.text)
		for system in systems_response_json: 
			system_list.append({'system_id':system['id'], 'system_name':system['sysname'], 'counter':counter})
			system_options.append(system['sysname'])
			counter+= 1


	project_or_policy_options = ['project', 'policy', 'DO NOT ADD']

	for current_result in downloaded_data_results:		
		
		project_or_policy_or_skip, project_or_policy_or_skip_index = pick(project_or_policy_options, 'Title:' + current_result['comment']+ '\nCategory:' + current_result['category'])

		if project_or_policy_or_skip_index != 2:
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
			submissions_to_upload.append({"projectorpolicy":project_or_policy_or_skip, "featuretype":"polygon", "description":diagram_description, "sysid":selected_system_id, "geojson":fc_to_upload})



	for current_submission_to_upload in submissions_to_upload:
		if config.apisettings['dryrun']:
			print(current_submission_to_upload)
		else:
			try:
				upload = myAPIHelper.post_as_diagram(geoms = current_submission_to_upload['geojson'], projectorpolicy= current_submission_to_upload['projectorpolicy'],featuretype = current_submission_to_upload['featuretype'], description= current_submission_to_upload['description'], sysid = current_submission_to_upload['sysid'] )
			except Exception as e: 
				print("Error in upload :" % e)
			else:
				print(upload.text)
			
			
