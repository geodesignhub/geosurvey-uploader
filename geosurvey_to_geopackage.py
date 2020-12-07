import json
import config
import requests
import math
import shapely
from shapely.geometry import shape, mapping, shape, asShape
import fiona, json
from fiona import collection
from fiona.crs import from_string

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


	schema_polygon = {
		'geometry': 'Polygon',
		'properties': {'id':'str', 'comment':'str','category':'str','date_added':'str'}
	}
	
	schema_polyline = {
		'geometry': 'LineString',
		'properties': {'id':'str', 'comment':'str','category':'str','date_added':'str'}
	}
	crs = from_string("+datum=WGS84 +ellps=WGS84 +no_defs +proj=longlat")

	with collection('downloaded_data_polygons.gpkg', 'w', driver='GPKG',crs=crs, layer = 'polygons',schema=schema_polygon) as c:		
		for curPoly in downloaded_data_results:
			s = asShape(curPoly['geojson']['geometry'])
			if s.geom_type == 'Polygon':
				c.write({
					'geometry': mapping(s),
					'properties': {'id': curPoly['id'], 'comment':curPoly['comment'], 'category':curPoly['category'], 'date_added':curPoly['date_added']}
					})
	
	with collection('downloaded_data_lines.gpkg', 'w', driver='GPKG',crs=crs, layer = 'polygons',schema=schema_polyline) as c:		
		for cur_line in downloaded_data_results:
			s = asShape(cur_line['geojson']['geometry'])
			if s.geom_type == 'LineString':
				c.write({
					'geometry': mapping(s),
					'properties': {'id': cur_line['id'], 'comment':cur_line['comment'], 'category':cur_line['category'], 'date_added':cur_line['date_added']}
					})