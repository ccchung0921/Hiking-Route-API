import urllib.request
import bs4 as bs
from flask import Flask,jsonify,make_response
from flask_restful import Api, Resource
import concurrent.futures
import time
import requests

app = Flask(__name__)
api = Api(app)


class HikingRoute(Resource):

    def __init__(self):
        self.base_url = "https://www.alltrails.com/hong-kong"
        self.base_url2 = "https://www.oasistrek.com/barrier_free_trails.php"
        self.base_url3 = "https://www.oasistrek.com/"
        self.fetch_link = []
        self.fetch()
        self.api_key = 'AIzaSyCdXWm3q1aKCiuTuZYBMvcefJWG11aWcHY'
        self.google_url = 'https://maps.googleapis.com/maps/api/geocode/json?address='
        self.response = []

    def fetch(self):
        sauce = urllib.request.urlopen(self.base_url2).read()
        soup = bs.BeautifulSoup(sauce, 'html.parser')
        routes = soup.find_all('div', {'class': 'travel', 'style': 'clear:both'})
        for route in routes:
            route_link = route.find('a')['href']
            self.fetch_link.append(route_link)

    def get_geocode(self,place):
        r = requests.get(self.google_url + place + '&key='+ self.api_key)
        geo_code = r.json()['results'][0]['geometry']['location']
        return geo_code

    def get_routes(self,routes):
        base_url = self.base_url3 + routes
        print(base_url)
        geopoints = []
        sauce = urllib.request.urlopen(base_url).read()
        soup = bs.BeautifulSoup(sauce, 'html.parser')
        trail = soup.find('div', {'class': 'trailcontent'})
        name = trail.find('div', {'class': 'banner'}).find('img')['alt']
        if name[:2] != '梅窩':
            time_need = trail.find_all('div', {'class': 'info'})[1]
            length = trail.find_all('div', {'class': 'info'})[2]
            route = trail.find('div', {'class': 'route'})
            locations = route.text.split("›")
            for location in locations:
                geopoints.append(self.get_geocode(location.strip()))
            if length:
                length = length.text[2:].strip()
            if time_need:
                time_need = time_need.text[2:].strip()
            star = trail.find('div', {'class': 'star'}).find('svg', {'class': 'star_new_1'})
            if star:
                default = 5
                difficulty = default - len(star.find_all('use', {'class': 'star--empty'}))
            self.response.append({
                "name": name,
                "difficulty": difficulty,
                "length": length,
                "time": time_need,
                "geopoints": geopoints
            })

    def concurrent(self):
        timer1 = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(self.get_routes, self.fetch_link)
        timer2 = time.perf_counter()
        print(f"process finished in {timer2-timer1} secs")

    def get(self):
        self.concurrent()
        return make_response(jsonify({
            'result': self.response,
            'status': 'OK',
        }), 200)


api.add_resource(HikingRoute, "/hiking")

if __name__ == '__main__':
    hiking = HikingRoute()
    app.run(debug=True)