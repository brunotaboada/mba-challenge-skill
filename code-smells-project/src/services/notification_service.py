import logging

log = logging.getLogger(__name__)


class LoggingNotifier:
    """Notifier que apenas registra eventos no log estruturado.

    Em produção, substituir por implementação que publica em fila/email.
    """

    def pedido_criado(self, usuario_id: int, pedido_id: int) -> None:
        log.info("Pedido criado", extra={"pedido_id": pedido_id, "usuario_id": usuario_id})

    def pedido_status_atualizado(self, pedido_id: int, status: str) -> None:
        log.info(
            "Status do pedido atualizado",
            extra={"pedido_id": pedido_id, "status": status},
        )
