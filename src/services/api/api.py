import pickle

import httpx

from ..base import Actor, Message, Sig, actor_system

from . import helpers
from ..settings import USERNAME, PASSWORD, extensions_all
from .constants import AUTH, NAS


class API(Actor):
    def __init__(self, pid: int, name='',parent: Actor=None) -> None:
        super().__init__(pid, name, parent)
        self.DEBUG = 0
        self.username = USERNAME
        self.password = PASSWORD
        self.token = None
        self.extensions = extensions_all

    def dispatch(self, sender: Actor, msg: Message) -> None:
        match msg.sig:
            case Sig.LOGIN:
                try:
                    response = httpx.post(
                        url=AUTH.LOGIN, 
                        json={
                            'username':self.username, 
                            'password': self.password
                        },
                        timeout=20.0
                    )
                except httpx.NetworkError as err:
                    actor_system.send(sender, Message(sig=Sig.NETWORK_FAILURE, args=str(err)))
                else:
                    self.token = response.json().get('token')
                    if self.token is None:
                        actor_system.send(sender, Message(sig=Sig.LOGIN_FAILURE, args=response.json()))
                    else:
                        actor_system.send(sender, Message(sig=Sig.LOGIN_SUCCESS))

            case Sig.EXT_SET:
                try:
                    response = httpx.patch(
                        url=NAS.EXT,
                        headers=helpers.get_headers(self.token),
                        json=list(self.extensions),
                        timeout=10.0
                    )
                except httpx.NetworkError as err:
                    actor_system.send(sender, Message(sig=Sig.NETWORK_FAILURE))
                else:
                    if response.status_code != 200:
                        actor_system.send(sender, Message(sig=Sig.NETWORK_FAILURE, args=response.json()))
                    else:
                        actor_system.send(sender, Message(sig=Sig.EXT_SET))

            case Sig.FILES_GET:
                try:
                    with open('cache.pckl', 'rb') as f:
                        data = pickle.load(f)
                except Exception:
                    try:
                        response: httpx.Response = httpx.get(
                            url=NAS.FILES,
                            headers=helpers.get_headers(self.token),
                            timeout=20.0
                        )
                    except httpx.NetworkError as err:
                        actor_system.send('Dispatcher', Message(sig=Sig.NETWORK_FAILURE, args=str(err)))
                    else:
                        if response.status_code != 200:
                            actor_system.send('Dispatcher', Message(sig=Sig.NETWORK_FAILURE, args=response.json()))
                        else:
                            data = response.json()
                            with open('cache.pckl', 'wb') as f:
                                pickle.dump(data, f)
                actor_system.send('Dispatcher', Message(sig=Sig.FILES_GET, args=data))
            
            case Sig.FILES_REINDEX:
                response: httpx.Response = httpx.patch(
                    url=NAS.FILES, 
                    headers=helpers.get_headers(self.token),
                    timeout=10.0
                )
                if response.status_code != 200:
                    raise Exception(f'{response.json()}')
                actor_system.send(sender, Message(sig=Sig.FILES_GET))

            case _:
                raise SystemExit(f'{msg=}')
