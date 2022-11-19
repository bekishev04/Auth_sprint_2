import abc

import requests

import authservice.schemas as schemas
import authservice.entrypoints.enums as enums
from authservice import cfg


class AbstractProvider:
    @abc.abstractmethod
    def authorize(self, code: str) -> str:
        pass

    @abc.abstractmethod
    def get_user_data(self, access_token: str) -> schemas.OAuthUser:
        pass


class ProviderVK(AbstractProvider):

    def get_user_data(self, access_token: str) -> schemas.OAuthUser | None:
        link = 'https://api.vk.com/method/users.get'
        params = {'access_token': access_token,
                  'v': '5.131'}
        resp = requests.get(link, params=params)
        try:
            json = resp.json()
        except requests.exceptions.JSONDecodeError:
            return None
        if json.get('error', None):
            return None
        json_resp = json['response'][0]
        schema = schemas.OAuthUser(user_id=json_resp.get('id'),
                                   login=json_resp.get('email', ''))
        return schema

    def authorize(self, code: str) -> str | None:
        link = 'https://oauth.vk.com/access_token'
        params = {'client_id': cfg.VK_APP_ID,
                  'client_secret': cfg.VK_CLIENT_SECRET,
                  'redirect_uri': cfg.VK_REDIRECT_URI,
                  'code': code}
        resp = requests.get(link, params=params)
        try:
            json = resp.json()
        except requests.exceptions.JSONDecodeError:
            return None
        if json.get('error', None):
            return None
        return json.get('access_token', None)


class ProviderYandex(AbstractProvider):

    def authorize(self, code: str) -> str | None:
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        params = {'grant_type': 'authorization_code',
                  'code': code,
                  'client_id': cfg.YANDEX_APP_ID,
                  'client_secret': cfg.YANDEX_CLIENT_SECRET}
        resp = requests.post('https://oauth.yandex.ru/token', headers=headers, data=params)
        try:
            json = resp.json()
        except requests.exceptions.JSONDecodeError:
            return None
        if json.get('error', None):
            return None
        return json.get('access_token', None)

    def get_user_data(self, access_token: str) -> schemas.OAuthUser | None:
        headers = {'Authorization': f'OAuth {access_token}'}
        params = {'format': 'json'}
        resp = requests.get('https://login.yandex.ru/info', params=params, headers=headers)
        try:
            json = resp.json()
        except requests.exceptions.JSONDecodeError:
            return None
        if json.get('error', None):
            return None
        schema = schemas.OAuthUser(user_id=json.get('id'),
                                   login=json.get('default_email', ''))
        return schema


def get_provider(provider: enums.ServiceProvider):
    providers = {enums.ServiceProvider.VK: ProviderVK(),
                 enums.ServiceProvider.YANDEX: ProviderYandex()}
    return providers.get(provider, None)
