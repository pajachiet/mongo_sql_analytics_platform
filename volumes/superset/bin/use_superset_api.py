import requests
from bs4 import BeautifulSoup


def get_csrf_token(raw_resp):
    soup = BeautifulSoup(raw_resp.text, 'html.parser')
    token = [n['value'] for n in soup.find_all('input')]
    return token[0]


class UseSupersetApi:
    def __init__(self, username=None, password=None):
        self.s = requests.Session()
        self.base_url = 'http://localhost:8088/'
        self._csrf = get_csrf_token(self.s.get(self.url('login/')))
        self.headers = {'X-CSRFToken': self._csrf, 'Referer': self.url('login/')}
        # note: does not use headers because of flask_wtf.csrf.validate_csrf
        # if data is dict it is used as form and ends up empty but flask_wtf checks if data ...
        self.s.post(self.url('login/'),
                    data={'username': username, 'password': password, 'csrf_token': self._csrf})

    def url(self, suffix):
        return self.base_url + suffix

    def get(self, suffix):
        return self.s.get(self.url(suffix), headers=self.headers)

    def post(self, url, data=None, **kwargs):
        if not data:
            data = {}
        data['csrf_token'] = self._csrf
        return self.s.post(self.url(url), data=data, **kwargs)
