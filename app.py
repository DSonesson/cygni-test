from werkzeug.utils import import_string
from flask import Flask, abort, jsonify

from aiohttp import ClientSession
import requests
import asyncio
import json

from aiocache import cached, Cache
from aiocache.serializers import PickleSerializer

app = Flask(__name__)

# Error handlers 

@app.errorhandler(400)
def resource_not_found(e):
    return jsonify(error=str(e)), 400

@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404
       
# Routes 

@app.route('/api/<mbid>')
@cached(ttl=300, cache=Cache.MEMORY, serializer=PickleSerializer())
async def entry(mbid):
    ## --------------------- ##
    # Entry point for the API.
    # Returns either a JSON response with the requested information or an HttpError
    ## --------------------- ##

    #First get the wikipedia title and album data
    wikipedia_title, mb_album_data = get_title_and_albums(mbid)
    wikipedia_description = get_wikipedia_description(wikipedia_title)
    coverart_albums = await get_album_covers(mb_album_data)

    response = {'mbid': mbid,
                'description': wikipedia_description,
                'albums': coverart_albums}

    return response

# Helper functions

def get_title_and_albums(mbid):
    ## --------------------- ##
    # Requests information from MusicBrainz API and wikidata
    # Returns the wikipedia title and album information from music brainz
    # or raises an error caught from either API.
    ## --------------------- ##
    mb_url = "http://musicbrainz.org/ws/2/artist/"    
    mb_request_url = mb_url + mbid
    mb_params = {'fmt' : 'json', 'inc' : 'url-rels+release-groups'}
    
    mb_request = requests.get(url = mb_request_url, params = mb_params)
    mb_data = mb_request.json()     
    
    if mb_request.status_code != requests.codes.ok:
        abort(mb_request.status_code, description="Error when requesting MusicBrainz API. Error message: " + mb_data['error'])

    mb_album_data = []
    for ent in mb_data['release-groups']:
        mb_album_data.append((ent['title'], ent['id']))

    #Filters the response to find either a wikipedia or wikidata type
    wikipedia_filter = list(filter(lambda x: x['type'] == 'wikipedia', mb_data['relations']))
    wikidata_filter = list(filter(lambda x: x['type'] == 'wikidata', mb_data['relations']))
    if wikipedia_filter:
        #TODO: Set wikipedia_title to correct value from entry
        #No example was found when this was true, so not sure how to extract the title here.
        print("Wikipedia filter not empty, able to find wikipedia title directly")
        print(wikipedia_filter[0])
    elif wikidata_filter:
        wikidata_band_id = wikidata_filter[0]['url']['resource'].split('/')[-1] #Splits the url and takes the last element, which should be the wikidata_id
        wikipedia_title = get_wikipedia_title(wikidata_band_id)
    else:
       abort(404, "Error, no wikidata ID or wikipedia title found in MusicBrainz response")

    return wikipedia_title, mb_album_data


def get_wikipedia_title(wikidata_band_id):
    ## --------------------- ##
    # Requests wikidata API with an ID to find the wikipedie title
    # Returns the wikipedia title for the english wikipedia or returns an error.
    ## --------------------- ##
    wikidata_url = "https://www.wikidata.org/w/api.php/"  
    wikidata_params = {'action':'wbgetentities', 'ids':wikidata_band_id, 'format':'json' , 'props':'sitelinks' }
    
    wikidata_request = requests.get(url = wikidata_url, params = wikidata_params)
    wikidata_data = wikidata_request.json()

    #The status code for the request seems to be 200 even if it's and invalid ID.
    #Statement below checks the first key in response as that seems to be 'error' if any error occured.
    if list(wikidata_data.keys())[0] == 'error':
        abort(400, "Error when requesting wikidata API. Error message: "+wikidata_data['error']['info'])

    wikipedia_title = wikidata_data['entities'][wikidata_band_id]['sitelinks']['enwiki']['title']
    
    return wikipedia_title

def get_wikipedia_description(wikipedia_title):
    ## --------------------- ##
    # Requests wikipedia API with an title to find wikipedia description
    # Returns the wikipedia title or 'not found' if no entry was found for the given title
    ## --------------------- ##
    wikipedia_url = "https://en.wikipedia.org/w/api.php/"
    
    wikipedia_params = {'action':'query', 'format':'json' , 'prop':'extracts', 'exintro':'true', 'redirects':'true', 'titles':wikipedia_title}
    wikipedia_request = requests.get(url = wikipedia_url, params = wikipedia_params)
    wikipedia_data = wikipedia_request.json()
    
    #If an invalid key was passed the page id seems to be '-1', hence the statement below.
    if list(wikipedia_data['query']['pages'].keys())[0] == '-1':
        wikipedia_description = "Wikipedia description not found for title: " + wikipedia_title
    else:
        #One key in the JSON seems to be a page ID, and is not the same for each response.
        #The for loop accesses that value without knowing the key.
        for value in wikipedia_data['query']['pages'].values():
            wikipedia_description = value['extract']
    
    return wikipedia_description

async def fetch_album_image(session, url):
    ## --------------------- ##
    # Help function for async fetches of the album images.
    ## --------------------- ##
    response = await session.get(url)
    return response

async def get_album_covers(mb_album_data):
    ## --------------------- ##
    # Requests CoverArtArchive API with MusicBrainz album data.
    # Returns a list with album ids, titles an image URLs.
    # Or an empty list if no album information is provided.
    ## --------------------- ##
    coverart_url = "http://coverartarchive.org/"
    coverart_albums = []
    
    if len(mb_album_data) == 0:
        coverart_albums.append("No album data found.")

    async with ClientSession() as session:
        tasks = []
        for ent in mb_album_data:
            album_title = ent[0]
            album_id = ent[1]             
            album_dict = {'title':album_title, 'id':album_id}
            coverart_albums.append(album_dict)

            coverart_request_url = coverart_url + 'release-group/' + album_id
            task = asyncio.create_task(fetch_album_image(session, coverart_request_url))
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)

        for i ,response in enumerate(responses):
            album_image = "Not found." #Some albums does not have any CoverArt infromation. This is the default value for those.
            if response.status == requests.codes.ok:
                res_dict = json.loads(await response.text())
                album_image = res_dict['images'][0]['image']
            coverart_albums[i]['image'] = album_image

    return coverart_albums