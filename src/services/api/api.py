import pickle
from typing import Optional
import logging

import httpx

from ..base import Actor, Message, Sig, actor_system, ActorGeneric

from . import helpers
from ...settings import USERNAME, PASSWORD, extensions_all
from .constants import AUTH, NAS


class API(Actor):
    def __init__(self, pid: int, parent: ActorGeneric, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.username = USERNAME
        # stockage d'un mdp non crypté dans une globale
        self.password = PASSWORD
        self.token: Optional[str] = None
        self.extensions = extensions_all
        # self.init_logger(__name__)
        # self.log_lvl = logging.INFO
        self.post(Message(sig=Sig.INIT))

    def dispatch(self, sender: Actor, msg: Message) -> None:
        response: httpx.Response
        match msg:
            case Message(sig=Sig.INIT, args=args):
                self.post(Message(Sig.LOGIN))

            case Message(sig=Sig.LOGIN_SUCCESS, args=args):
                self.post(Message(Sig.EXT_SET))

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
                    # network error, introspection for cause, possible recovery
                    actor_system.send('Dispatcher', Message(sig=Sig.NETWORK_FAILURE, args=str(err)))
                else:
                    self.token = response.json().get('token')
                    if self.token is None:
                        # too broad, asses for username or password failure and api failure, recovery possible
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
                        response = httpx.get(
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
                response = httpx.patch(
                    url=NAS.FILES, 
                    headers=helpers.get_headers(self.token),
                    timeout=10.0
                )
                if response.status_code != 200:
                    raise Exception(f'{response.json()}')
                self.post(Message(sig=Sig.FILES_GET))

            case Message(sig=Sig.AUDIT, args=None):
                actor_system.send(sender, {'event': 'audit', 'data': self.introspect()})

            case Message(sig=Sig.SIGQUIT):
                self.terminate()

            case _:
                raise SystemExit(f'{msg=}')
