import unittest
import json
from flask import jsonify
from werkzeug.exceptions import BadRequest

from app import app, get_wikipedia_title, get_wikipedia_description, get_album_covers


class ApiTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()      

    def test_valid_mbid(self):
        # Test the API with a valid mbid. 
        # API should return status 200 and should have filled fields for 
        # albums and description. 
        mbid = "65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab" #Should be valid
        response = self.app.get("/api/"+mbid)
        response_dict = json.loads((response.data.decode('utf-8')))

        self.assertEqual(200, response.status_code)
        self.assertTrue("No album data found." not in response_dict['albums'][0])
        self.assertTrue("Wikipedia description not found for title: " not in response_dict['description'])

    def test_invalid_mbid(self):
        # Test the API with an invalid mbid.
        # API should return status 400.
        mbid = "abcde"
        response = self.app.get("/api/"+mbid)
        self.assertEqual(400, response.status_code)

    def test_get_wikipedia_title_with_valid_band_id(self):
        # Test the get_wikipedia_title function with a valid band id.
        # In this case the band id should belong to 'Metallica'.
        band_id = "Q15920"
        response = get_wikipedia_title(band_id)
        self.assertEqual("Metallica", response)

    def test_get_wikipedia_title_with_invalid_band_id(self):
        # Test the get_wikipedia_title function with an invalid band id.
        # Function should return a "bad request" status code.
        band_id = "123abc"
        try:
            get_wikipedia_title(band_id)
        except Exception as e:
            self.assertEqual(type(e), BadRequest)

    def test_get_wikipedia_description_with_invalid_title(self):
        # Test the get_wikipedia_description function with an invalid wikipedia title.
        # Function should return "Wikipedia description not found" string.
        title = 'xxxxxx'
        response = get_wikipedia_description(title)
        self.assertTrue("Wikipedia description not found" in response)

    async def test_get_get_album_covers_with_empty_album_data(self):
        # Test the get_album_covers with an empty list of album ids.
        # Function should return a list with string "No album data found."
        album_data = []
        response = await get_album_covers(album_data)
        print(response)
        self.assertTrue("No album data found." in response[0])

    async def test_get_get_album_covers_with_invalid_album_data_id(self):
        # Test the get_album_covers with a list of invalid album ids.
        # Function should return "Not found." for the image field.
        album_data = [["Album_name", "xxxx"]]
        response = await get_album_covers(album_data)
        self.assertEqual("Not found.", response[0]['image'])

