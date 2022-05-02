import pickle

import httpx

from ..base import Actor, Message, Sig, actor_system

from . import helpers
from ...settings import USERNAME, PASSWORD, extensions_all
from .constants import AUTH, NAS


class API(Actor):
    def __init__(self, pid: int, name='', parent: Actor|None=None, **kwargs) -> None:
        super().__init__(pid, name, parent, **kwargs)
        self.LOG = 0
        self.username = USERNAME
        # stockage d'un mdp non crypté dans une globale
        self.password = PASSWORD
        self.token = None
        self.extensions = extensions_all
        self.post(self, Message(sig=Sig.INIT))

    def dispatch(self, sender: Actor, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.INIT, args=args):
                self.post(self, Message(Sig.LOGIN))

            case Message(sig=Sig.LOGIN_SUCCESS, args=args):
                self.post(self, Message(Sig.EXT_SET))

            case Message(sig=Sig.LOGIN_FAILURE, args=args):
                actor_system.send('Dispatcher', Message(sig=Sig.LOGIN_FAILURE, args=str(err)))

            case Message(sig=Sig.LOGIN, args=args):
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
                    actor_system.send('Dispatcher', Message(sig=Sig.NETWORK_FAILURE, args=str(err)))
                else:
                    self.token = response.json().get('token')
                    if self.token is None:
                        actor_system.send(sender, Message(sig=Sig.LOGIN_FAILURE, args=response.json()))
                    else:
                        actor_system.send(sender, Message(sig=Sig.LOGIN_SUCCESS))

            case Message(sig=Sig.EXT_SET, args=args):
                try:
                    response = httpx.patch(
                        url=NAS.EXT,
                        headers=helpers.get_headers(self.token),
                        json=list(self.extensions),
                        timeout=10.0
                    )
                except httpx.NetworkError as err:
                    actor_system.send('Dispatcher', Message(sig=Sig.NETWORK_FAILURE))
                else:
                    if response.status_code != 200:
                        actor_system.send('Dispatcher', Message(sig=Sig.NETWORK_FAILURE, args=response.json()))
                    else:
                        actor_system.send(sender, Message(sig=Sig.FILES_GET))

            case Message(sig=Sig.FILES_GET, args=args):
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
                actor_system.send('Files', Message(sig=Sig.FILES_NEW, args=data))
            
            case Message(sig=Sig.FILES_REINDEX, args=args):
                response: httpx.Response = httpx.patch(
                    url=NAS.FILES, 
                    headers=helpers.get_headers(self.token),
                    timeout=10.0
                )
                if response.status_code != 200:
                    raise Exception(f'{response.json()}')
                self.post(sender, Message(sig=Sig.FILES_GET))
                # actor_system.send(sender, Message(sig=Sig.FILES_GET))

            case _:
                raise SystemExit(f'{msg=}')
