import requests, json, GeodesignHub, config, geojson
from pick import pick
# A sample script to take a diagram from Geodesign Hub, buffer it and send
# it back as a new diagram using the API.
#

if __name__ == "__main__":
	
	myAPIHelper = GeodesignHub.GeodesignHubClient(url = config.apisettings['serviceurl'], project_id=config.apisettings['projectid'], token=config.apisettings['apitoken'])
	counter =0

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
	
	with open('data.json', 'r') as geoforage_data: 
		downloaded_data = geoforage_data.read()
	dd = json.loads(downloaded_data)
	downloaded_data_results = dd['results']
	geometries_to_upload = []
	
	for current_result in downloaded_data_results:		
		
		project_or_policy_or_skip, project_or_policy_or_skip_index = pick(project_or_policy_options, 'Title:' + current_result['comment']+ '\nCategory:' + current_result['category'])

		if project_or_policy_or_skip_index != 2:
			selected_system_option, selected_system_index = pick(system_options, 'Title:' + current_result['comment'] + '\nCategory:' + current_result['category'])
			system_list_filtered = list(filter(lambda x: x['counter'] == selected_system_index, system_list))
			selected_system_id = system_list_filtered[0]['system_id']

			geometries_to_upload.append({'projectorpolicy':project_or_policy_or_skip, "featuretype":'polygon', 'description':current_result['comment'], 'sysid':selected_system_id, 'geojson':current_result['geojson']})



	for current_geometry_to_upload in geometries_to_upload:
		if config.apisettings['dryrun']:
			print(geojson.loads(json.dumps(current_geometry_to_upload['geojson'])))
			# print(json.dumps(current_geometry_to_upload['geometry']))
		else:
			# upload = myAPIHelper.post_as_diagram(geoms = current_geometry_to_upload['geometry'], projectorpolicy= current_geometry_to_upload['projectorpolicy'],featuretype = 'polygon', description= current_geometry_to_upload['geojson'], sysid = current_geometry_to_upload['sysid'] )
			# print(upload.text)
			pass
