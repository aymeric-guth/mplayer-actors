import asyncio
from asyncore import dispatcher

import httpx

from ..base import Actor, Message, Sig
from . import helpers
from ..settings import USERNAME, PASSWORD, extensions_all


BASE_URL = "https://ars-virtualis.org/api"
BASE = f"{BASE_URL}/nas"

# class NAS(object):
#     BASE: str = f"{BASE_URL}/nas"
#     FILES: str = f"{BASE}/files"
#     PLAYBACK: str = f"{BASE}/playback"
# current, sender, message, dest

class API(Actor):
    def __init__(self, parent: Actor) -> None:
        super().__init__()
        self.DEBUG = 0
        self.parent = parent
        self.username = USERNAME
        self.password = PASSWORD
        self.token = None
        self.extensions = extensions_all

    def run(self) -> None:
        while 1:
            (actor, msg) = self.mq.get()
            self.debug(msg, actor)

            match msg.sig:
                case Sig.LOGIN:
                    try:
                        response = httpx.post(
                            url=f'{BASE_URL}/authentication/login', 
                            json={
                                'username':self.username, 
                                'password': self.password
                            },
                            timeout=20.0
                        )
                    except httpx.NetworkError as err:
                        actor.post(self, Message(sig=Sig.NETWORK_FAILURE, args=str(err)))
                    else:
                        self.token = response.json().get('token')
                        if self.token is None:
                            actor.post(self, Message(sig=Sig.LOGIN_FAILURE, args=response.json()))
                        else:
                            actor.post(self, Message(sig=Sig.LOGIN_SUCCESS))

                case Sig.EXT_SET:
                    try:
                        response = httpx.patch(
                            url=f"{BASE}/extensions",
                            headers=helpers.get_headers(self.token),
                            json=list(self.extensions),
                            timeout=10.0
                        )
                    except httpx.NetworkError as err:
                        actor.post(self, Message(sig=Sig.NETWORK_FAILURE))
                    else:
                        if response.status_code != 200:
                            actor.post(self, Message(sig=Sig.NETWORK_FAILURE, args=response.json()))
                        else:
                            actor.post(self, Message(sig=Sig.EXT_SET))

                case Sig.FILES_GET:
                    dispatcher = self.get_actor('Dispatcher')
                    try:
                        response: httpx.Response = httpx.get(
                            url=f'{BASE}/files',
                            headers=helpers.get_headers(self.token),
                            timeout=20.0
                        )
                    except httpx.NetworkError as err:
                        # -> dispatcher
                        dispatcher.post(self, Message(sig=Sig.NETWORK_FAILURE, args=str(err)))
                    else:
                        if response.status_code != 200:
                            # -> dispatcher
                            dispatcher.post(self, Message(sig=Sig.NETWORK_FAILURE, args=response.json()))
                        else:
                            # -> dispatcher
                            dispatcher.post(self, Message(sig=Sig.FILES_GET, args=response.json()))
                
                case Sig.FILES_REINDEX:
                    response: httpx.Response = httpx.patch(
                        url=f'{BASE}/files', 
                        headers=helpers.get_headers(self.token),
                        timeout=10.0
                    )
                    if response.status_code != 200:
                        raise Exception(f'{response.json()}')
                    self.post(self, Message(sig=Sig.FILES_GET))

                case Sig.REGISTER:
                    self.register(actor)

                case _:
                    raise SystemExit(f'{msg=}')

            self.mq.task_done()
