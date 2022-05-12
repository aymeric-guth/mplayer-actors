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
        self.token = ''
        self.extensions = extensions_all
        self.post(Message(sig=Sig.INIT))

    def dispatch(self, sender: ActorGeneric, msg: Message) -> None:
        response: httpx.Response
        match msg:
            case Message(sig=Sig.INIT, args=args):
                self.post(Message(Sig.LOGIN))

            case Message(sig=Sig.LOGIN_SUCCESS, args=token):
                self.token = token
                self.post(Message(Sig.EXT_SET, args=list(self.extensions)))

            case Message(sig=Sig.LOGIN_FAILURE, args=args):
                actor_system.send('Dispatcher', Message(sig=Sig.LOGIN_FAILURE, args=args))

            case Message(sig=Sig.EXT_SUCCESS, args=args):
                actor_system.send('External', Message(sig=Sig.GET_CACHE))

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
                    token = response.json().get('token')
                    if token is None:
                        self.post(Message(sig=Sig.LOGIN_FAILURE, args=response.json()))
                    else:
                        self.post(Message(sig=Sig.LOGIN_SUCCESS, args=token))

            case Message(sig=Sig.EXT_SET, args=extensions):
                try:
                    response = httpx.patch(
                        url=NAS.EXT,
                        headers=helpers.get_headers(self.token),
                        json=extensions,
                        timeout=10.0
                    )
                except httpx.NetworkError as err:
                    actor_system.send('Dispatcher', Message(sig=Sig.NETWORK_FAILURE, args=str(err)))
                else:
                    if response.status_code != 200:
                        actor_system.send('Dispatcher', Message(sig=Sig.NETWORK_FAILURE, args=response.json()))
                    else:
                        self.post(Message(sig=Sig.EXT_SUCCESS))
            
            case Message(sig=Sig.FILES_GET, args=args):
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
                        actor_system.send('External', Message(sig=Sig.FILES_NEW, args=response.json()))

            case Message(sig=Sig.FILES_REINDEX, args=args):
                try:
                    response = httpx.patch(
                        url=NAS.FILES, 
                        headers=helpers.get_headers(self.token),
                        timeout=10.0
                    )
                except httpx.NetworkError as err:
                    actor_system.send('Dispatcher', Message(sig=Sig.NETWORK_FAILURE, args=str(err)))
                else:
                    if response.status_code != 200:
                        actor_system.send('Dispatcher', Message(sig=Sig.NETWORK_FAILURE, args=response.json()))
                    else:
                        self.post(Message(sig=Sig.FILES_GET))

            case Message(sig=Sig.SIGQUIT):
                self.terminate()

            case _:
                raise SystemExit(f'{msg=}')
