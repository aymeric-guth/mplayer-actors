import logging

import httpx

from actors import Actor, Message, Sig, send, DispatchError, ActorException, SystemMessage, Request, Response

from . import helpers
from ...settings import USERNAME, PASSWORD, extensions_all
from .constants import AUTH, NAS


class API(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.username = USERNAME
        # stockage d'un mdp non crypté dans une globale
        self.password = PASSWORD
        self.token = ''
        self.extensions = extensions_all
        self.log_lvl = logging.ERROR

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return
        
        response: httpx.Response
        match msg:
            case Message(sig=Sig.LOGIN_SUCCESS, args=token):
                self.token = token
                send(self.pid, Message(Sig.EXT_SET, args=list(self.extensions)))

            case Message(sig=Sig.LOGIN_FAILURE, args=args):
                raise ActorException(args)

            case Message(sig=Sig.NETWORK_FAILURE, args=args):
                raise ActorException(args)

            case Message(sig=Sig.EXT_SUCCESS, args=args):
                send('External', Message(sig=Sig.GET_CACHE))

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
                    send(self.pid, Message(sig=Sig.NETWORK_FAILURE, args=str(err)))
                else:
                    token = response.json().get('token')
                    if token is None:
                        send(self.pid, Message(sig=Sig.LOGIN_FAILURE, args=response.json()))
                    else:
                        send(self.pid, Message(sig=Sig.LOGIN_SUCCESS, args=token))

            case Message(sig=Sig.EXT_SET, args=extensions):
                try:
                    response = httpx.patch(
                        url=NAS.EXT,
                        headers=helpers.get_headers(self.token),
                        json=extensions,
                        timeout=10.0
                    )
                except httpx.NetworkError as err:
                    send(self.pid, Message(sig=Sig.NETWORK_FAILURE, args=str(err)))
                else:
                    if response.status_code != 200:
                        send(self.pid, Message(sig=Sig.NETWORK_FAILURE, args=response.json()))
                    else:
                        send(self.pid, Message(sig=Sig.EXT_SUCCESS))
            
            case Message(sig=Sig.FILES_GET, args=args):
                try:
                    response = httpx.get(
                        url=NAS.FILES,
                        headers=helpers.get_headers(self.token),
                        timeout=20.0
                    )
                except httpx.NetworkError as err:
                    send(self.pid, Message(sig=Sig.NETWORK_FAILURE, args=str(err)))
                else:
                    if response.status_code != 200:
                        send(self.pid, Message(sig=Sig.NETWORK_FAILURE, args=response.json()))
                    else:
                        send('External', Message(sig=Sig.FILES_NEW, args=response.json()))

            case Message(sig=Sig.FILES_REINDEX, args=args):
                try:
                    response = httpx.patch(
                        url=NAS.FILES, 
                        headers=helpers.get_headers(self.token),
                        timeout=10.0
                    )
                except httpx.NetworkError as err:
                    send(self.pid, Message(sig=Sig.NETWORK_FAILURE, args=str(err)))
                else:
                    if response.status_code != 200:
                        send(self.pid, Message(sig=Sig.NETWORK_FAILURE, args=response.json()))
                    else:
                        send(self.pid, Message(sig=Sig.FILES_GET))

            case Request(type='get', name='file', args=args):
                try:
                    response = httpx.post(
                        url=NAS.FILES,
                        headers=helpers.get_headers(self.token),
                        json=args,
                        timeout=20.0
                    )
                except httpx.NetworkError as err:
                    send(self.pid, Message(sig=Sig.NETWORK_FAILURE, args=str(err)))
                else:
                    if response.status_code != 200:
                        send(self.pid, Message(sig=Sig.NETWORK_FAILURE, args=response.json()))
                    else:
                        send(to=sender, what=Response(type='get', name='file', args=response.content))
                        # send('External', Message(sig=Sig.FILES_NEW, args=response.json()))

            case _:
                raise DispatchError(f'Unprocessable msg={msg}')


    def init(self) -> None:
        send(self.pid, Message(Sig.LOGIN))
