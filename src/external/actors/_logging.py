# from typing import Optional

# from .message import Message


# def log_mq(self, sender: Optional[int], msg: Message) -> None:
#     if not isinstance(sender, int):
#         self.logger.error(f'### MQ ###\nGot unexpected Sender={sender}, type={type(sender)}\nmsg={msg}')
#     elif self.pid == sender:
#         self.logger.info(f'### MQ ###\nself={self!r}\n{msg=}')
#     else:
#         self.logger.info(f'### MQ ###\nreceiver={self!r}\nsender={actor_system.resolve_parent(sender).__repr__()}\n{msg=}')

# def log_post(self, sender: Optional[int], msg: Message) -> None:
#     if not isinstance(sender, int):
#         self.logger.error(f'### POST ###\nGot unexpected Sender={sender}, type={type(sender)}\nmsg={msg}')
#     elif self.pid == sender:
#         self.logger.info(f'### POST ###\nself={self!r}\n{msg=}')
#     else:
#         self.logger.info(f'### POST ###\nreceiver={self!r}\nsender={actor_system.resolve_parent(sender).__repr__()}\n{msg=}')