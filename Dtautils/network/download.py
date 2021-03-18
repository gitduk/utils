import requests


class Response(requests.Response):
    def __init__(self, response):
        self.response = response
