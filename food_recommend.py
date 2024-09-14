import requests
import os
from dotenv import load_dotenv
load_dotenv()

def get_coordinates(address, api_key):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': address,
        'key': api_key
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        results = response.json().get('results')
        if results:
            location = results[0]['geometry']['location']
            return location['lat'], location['lng']
    return None



def recommend(longitude,latitude):
    url = 'https://disco.deliveryhero.io/listing/api/v1/pandora/vendors'
    query = {
        'longitude':longitude,  # 經度
        'latitude': latitude,  # 緯度
        'language_id': 6,
        'include': 'characteristics',
        'dynamic_pricing': 0,
        'configuration': 'Variant1',
        'country': 'tw',
        'budgets': '',
        'cuisine': '164,201',
        'sort': 'distance_asc',
        'food_characteristic': '',
        'use_free_delivery_label': False,
        'vertical': 'restaurants',
        'limit': 10,
        'offset': 0,
        'customer_type': 'regular'
    }
    headers = {
        'x-disco-client-id': 'web',
    }
    r = requests.get(url=url, params=query, headers=headers)
    restaurant_list = []
    address_dict = {}
    if r.status_code == requests.codes.ok:
        data = r.json()
        restaurants = data['data']['items']
        for restaurant in restaurants:
            restaurant_list.append(restaurant["name"])
            address_dict[restaurant["name"]] = restaurant["address"]
    else:
        print("no restaurant "+restaurant_list)
    return restaurant_list, address_dict


if __name__ == "__main__":
    api_key = os.getenv("api_key")
    road_name = '花美男'


    latitude, longitude = get_coordinates(road_name, api_key)
    # if latitude and longitude:
    #     print(f"Latitude: {latitude}, Longitude: {longitude}")
    # else:
    #     print("Coordinates not found")
    
    # print(recommend(longitude, latitude))