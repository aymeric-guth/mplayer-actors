import logging

import httpx

from actors import (
    Actor,
    Message,
    send,
    DispatchError,
    ActorException,
    SystemMessage,
    Request,
    Response,
    Event,
)

from . import helpers
from ...settings import USERNAME, PASSWORD, extensions_all
from .constants import AUTH, NAS

from ._types import FileEntry


class API(Actor):
    def __init__(self, pid: int, parent: int, name="", **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.username = USERNAME
        # stockage d'un mdp non crypté dans une globale
        self.password = PASSWORD
        self.token = ""
        self.extensions = extensions_all
        self.log_lvl = logging.ERROR

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return

        response: httpx.Response
        match msg:
            case Event(type="success", name="login", args=token):
                self.token = token
                send(
                    to=self.pid,
                    what=Request(type="api", name="ext", args=list(self.extensions)),
                )

            case Event(type="failure", name="login", args=args):
                raise ActorException(args)

            case Event(type="failure", name="network", args=args):
                raise ActorException(args)

            case Event(type="success", name="ext"):
                send(to="External", what=Request(type="files", name="cache"))

            case Event(type="success", name="reindex"):
                send(to=self.pid, what=Request(type="api", name="files"))

            case Event(type="files", name="cache-empty"):
                send(to=self.pid, what=Request(type="api", name="files"))

            case Request(type="api", name="login"):
                try:
                    response = httpx.post(
                        url=AUTH.LOGIN,
                        json={"username": self.username, "password": self.password},
                        timeout=20.0,
                    )
                except httpx.NetworkError as err:
                    # network error, introspection for cause, possible recovery
                    send(
                        to=self.pid,
                        what=Event(type="failure", name="network", args=str(err)),
                    )
                else:
                    token = response.json().get("token")
                    if token is None:
                        send(
                            to=self.pid,
                            what=Event(
                                type="failure", name="login", args=response.json()
                            ),
                        )
                    else:
                        send(
                            to=self.pid,
                            what=Event(type="success", name="login", args=token),
                        )

            case Request(type="api", name="ext", args=extensions):
                try:
                    response = httpx.patch(
                        url=NAS.EXT,
                        headers=helpers.get_headers(self.token),
                        json=extensions,
                        timeout=10.0,
                    )
                except httpx.NetworkError as err:
                    send(
                        to=self.pid,
                        what=Event(type="failure", name="network", args=str(err)),
                    )
                else:
                    if response.status_code != 200:
                        send(
                            to=self.pid,
                            what=Event(
                                type="failure", name="network", args=response.json()
                            ),
                        )
                    else:
                        send(to=self.pid, what=Event(type="success", name="ext"))

            case Response(type="files", name="cache", args=data):
                send(to="Files", what=Event(type="files", name="new-data", args=data))

            case Request(type="api", name="files"):
                try:
                    response = httpx.get(
                        url=NAS.FILES,
                        headers=helpers.get_headers(self.token),
                        timeout=20.0,
                    )
                except httpx.NetworkError as err:
                    send(
                        to=self.pid,
                        what=Event(type="failure", name="network", args=str(err)),
                    )
                else:
                    if response.status_code != 200:
                        send(
                            to=self.pid,
                            what=Event(
                                type="failure", name="network", args=response.json()
                            ),
                        )
                    else:
                        send(
                            to="External",
                            what=Event(
                                type="files", name="new-data", args=response.json()
                            ),
                        )

            case Request(type="api", name="reindex"):
                try:
                    response = httpx.patch(
                        url=NAS.FILES,
                        headers=helpers.get_headers(self.token),
                        timeout=10.0,
                    )
                except httpx.NetworkError as err:
                    send(
                        to=self.pid,
                        what=Event(type="failure", name="network", args=str(err)),
                    )
                else:
                    if response.status_code != 200:
                        send(
                            to=self.pid,
                            what=Event(
                                type="failure", name="network", args=response.json()
                            ),
                        )
                    else:
                        send(to=self.pid, what=Event(type="success", name="reindex"))

            case Response(type="files", name="content", args=args):
                (arg, *_) = args
                self.logger.error(f"{arg}")
                self.logger.error(f"{arg.to_json()}")
                try:
                    response = httpx.patch(
                        url=NAS.PURGE_ONE,
                        headers=helpers.get_headers(self.token),
                        json=FileEntry.from_array(arg).to_json(),
                        timeout=10.0,
                    )
                except httpx.NetworkError as err:
                    send(
                        to=self.pid,
                        what=Event(type="failure", name="network", args=str(err)),
                    )
                else:
                    if response.status_code != 200:
                        send(
                            to=self.pid,
                            what=Event(
                                type="failure", name="network", args=response.json()
                            ),
                        )
                    else:
                        send(to=self.pid, what=Event(type="success", name="ext"))

            case Request(type="api", name="delete", args=args):
                send(to="Files", what=Request(type="files", name="content", args=args))

            case _:
                raise DispatchError(f"Unprocessable msg={msg}")

    def init(self) -> None:
        send(to=self.pid, what=Request(type="api", name="login"))


# with httpx.stream("GET", "https://www.example.com") as response:
