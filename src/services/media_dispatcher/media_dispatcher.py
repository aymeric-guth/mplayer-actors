from queue import Queue

from ..base import Actor, Message, Sig


class MediaDispatcher(Actor):
    def __init__(self) -> None:
        super().__init__()
        self.playlist = Queue()

    def run(self) -> None:
        # reçoit les fichiers a ajouter en queue
        # contact le bon service pour jouer le fichier en position 0
        # est signalé par les services media quand un fichier a terminé
        #   le cas échéant pop un fichier de la queue et l'envoi au service adéquat
        # en cas d'ajout de nouveaux fichiers (via commande play)
        #   signale tous les services media d'arreter la lecture
        #   dispatch le premier element au service adequat
        # comment assurer qu'un seul fichier est lu ?
        # comment assurer que le service media quitte bien en cas de msg exit
        
        while 1:
            (actor, msg) = self.mq.get()
            self.debug(msg, actor)

            match msg.sig:
                case Sig.INIT:
                    ...

                case Sig.REGISTER:
                    self.register(actor)

                case _:
                    raise SystemExit(f'{msg=}')
