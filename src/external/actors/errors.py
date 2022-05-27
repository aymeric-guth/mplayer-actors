class ActorException(Exception):
    ...


class DispatchError(Exception):
    ...


class ActorNotFound(ActorException):
    ...


class SystemMessage(ActorException):
    ...
