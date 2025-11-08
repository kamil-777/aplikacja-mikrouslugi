import os
import json
import pika

AMQP_URL = os.getenv("AMQP_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE = "health.events"

def _conn():
    params = pika.URLParameters(AMQP_URL)
    return pika.BlockingConnection(params)

def publish(routing_key: str, payload: dict):
    """Publikuj event jako topic."""
    conn = _conn()
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    ch.basic_publish(
        exchange=EXCHANGE,
        routing_key=routing_key,
        body=json.dumps(payload).encode("utf-8"),
        properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
    )
    conn.close()

def consume(queue: str, binding_keys: list[str], handler):
    """Konsumuj eventy i wywołuj handler(payload_dict)."""
    conn = _conn()
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    ch.queue_declare(queue=queue, durable=True)
    for key in binding_keys:
        ch.queue_bind(exchange=EXCHANGE, queue=queue, routing_key=key)

    def _cb(ch_, method, props, body):
        data = json.loads(body.decode("utf-8"))
        handler(data)
        ch_.basic_ack(delivery_tag=method.delivery_tag)

    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=queue, on_message_callback=_cb)
    ch.start_consuming()
