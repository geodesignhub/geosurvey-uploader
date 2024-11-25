import config
import requests
import math

from shapely.geometry import mapping, shape
import json
from fiona import collection
from fiona.crs import from_string
from pathlib import Path

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

	Path("downloaded_data").mkdir(parents=True, exist_ok=True)
	
	with collection('downloaded_data/downloaded_data_polygons.gpkg', 'w', driver='GPKG',crs=crs, layer = 'polygons',schema=schema_polygon) as c:		
		for curPoly in downloaded_data_results:
			s = shape(curPoly['geojson']['geometry'])
			
			if s.geom_type == 'MultiPolygon':
				polygons = list(s)
				for poly in polygons:
					c.write({
						'geometry': mapping(poly),
						'properties': {'id': curPoly['id'], 'comment':curPoly['comment'], 'category':curPoly['category'], 'date_added':curPoly['date_added']}
						})
			elif s.geom_type == 'Polygon':
				c.write({
					'geometry': mapping(s),
					'properties': {'id': curPoly['id'], 'comment':curPoly['comment'], 'category':curPoly['category'], 'date_added':curPoly['date_added']}
					})
	
	with collection('downloaded_data/downloaded_data_lines.gpkg', 'w', driver='GPKG',crs=crs, layer = 'polygons',schema=schema_polyline) as c:		
		for cur_line in downloaded_data_results:
			s = shape(cur_line['geojson']['geometry'])
			if s.geom_type == 'LineString':
				c.write({
					'geometry': mapping(s),
					'properties': {'id': cur_line['id'], 'comment':cur_line['comment'], 'category':cur_line['category'], 'date_added':cur_line['date_added']}
					})