# cygni-mashup

A backend written in Flask that takes an MusicBrainz identifier (mbid) of a band or artist and returns a JSON consisting of the MBID, a Wikipedia description and a list of all albums with title, id and cover image.

Uses MusicBrainz API, WikiData API, Wikipedia API and CoverArtArchive API.

## Setup
1. Make sure Python3 is installed
2. Copy the repository and navigate to it
3. Create a python virtual environment, eg ```python3 -m venv <path_to__virtual_env>```
4. activate virtual environment, eg ```source <path_to_virtual_env>/bin/activate```
5. Install requirements.txt, eg ```pip install -r requirements.txt```

## Start and test the server
To start the server, navigate to the root path. Make sure the virtual environment is actiaved and all requirements are installed.
To run the server use command ```flask run```
The server should be running on http://127.0.0.1:5000/ 
A call to the API should look like: http://127.0.0.1:5000/api/65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab

There are some tests for the api. These are  implemented using 'unittest'.
To run the tests use: ```python -m unittest tests/test_api.py```
There are some warnings when running the tests realted to the async get_album_covers function. However, the tests are all passed.

## Caching
Caching was implemented and functional. However when async was implemented the implementation broke, therefore it is removed for now.
TODO: Implement cache that works with async functions.

## Övrigt - now in swedish
Detta API är en uppdaterad version av ett tidigare test gjort, då implementerat i Django.

Jag lyckades inte hitta något fall där Wikipedia var med direkt i svaret från MusicBrainz, så denna funktion är inte helt fungerande. Jag har implementerat så att den kollar efter det, men jag vet inte hur det ska hanteras när man väl hittar något.

Om ingen wikipedia titel eller album-omslag hittas så sätts dessa värden till 'Not Found' i retur-JSON. Har kan man såklart välja att skicka tillbaka ett fel istället, men jag tyckte detta va en bättre lösning. 

Efter tidigare kommentarer valde jag att använda Flask denna gång. Och jag håller med tidigare kommentarer om att Django är ett onödigt stort ramverk för en uppgift av denna storlek, därför var flask ett bättre val.


