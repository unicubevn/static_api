import stomp
from dotenv import dotenv_values
from fastapi import APIRouter, Body
import pika
from pydantic import BaseModel

from model.fibonanci import FibonacciRpcClient

router = APIRouter(prefix="/v1", tags=["Producer"])
env = dotenv_values(".env")
rmq_credentials = pika.PlainCredentials(env["RABBITMQ_USER"], env["RABBITMQ_PASS"])
@router.post("/named")
def send_message_to_named_queue(
    queue: str = "service_A",
    message: str = "Message 1",
):
    """Send message to a named queue on RabbitMQ"""

    parameters = pika.ConnectionParameters(host=env["RABBITMQ_HOST"], port=env["RABBITMQ_PORT"],
                                           credentials=rmq_credentials, virtual_host=env["RABBITMQ_VHOST"])

    with pika.BlockingConnection(parameters) as connection:
        channel = connection.channel()

        channel.queue_declare(queue=queue)

        channel.basic_publish(exchange="", routing_key=queue, body=message)

    return {"sent": message}


@router.post("/worker")
def send_message_to_worker_queue(
    queue: str = "service_B",
    message: str = "Task 1",
):
    """Send message to a worker queue on RabbitMQ"""

    parameters = pika.ConnectionParameters(host=env["RABBITMQ_HOST"], port=env["RABBITMQ_PORT"],
                                           credentials=rmq_credentials,virtual_host=env["RABBITMQ_VHOST"])

    with pika.BlockingConnection(parameters) as connection:
        channel = connection.channel()

        channel.queue_declare(queue=queue)

        channel.basic_publish(exchange="", routing_key=queue, body=message)

    return {"sent": message}


@router.post("/pubsub")
def send_message_to_subscribers(
    exchange: str = "logs",
    message: str = "Log 1",
):
    """Send message to a fanout exchange on RabbitMQ"""

    parameters = pika.ConnectionParameters(host=env["RABBITMQ_HOST"], port=env["RABBITMQ_PORT"],
                                           credentials=rmq_credentials,virtual_host=env["RABBITMQ_VHOST"])

    with pika.BlockingConnection(parameters) as connection:
        channel = connection.channel()

        channel.exchange_declare(exchange=exchange, exchange_type="fanout")

        channel.basic_publish(exchange=exchange, routing_key="", body=message)

    return {"sent": message}


@router.post("/routing")
def send_message_to_specific_subscribers(
    exchange: str = "direct_logs",
    message: str = "Log 1",
    routing_key: str = "critical",
):
    """Send message to a direct exchange on RabbitMQ"""

    parameters = pika.ConnectionParameters(host=env["RABBITMQ_HOST"], port=env["RABBITMQ_PORT"],
                                           credentials=rmq_credentials,virtual_host=env["RABBITMQ_VHOST"])

    with pika.BlockingConnection(parameters) as connection:
        channel = connection.channel()

        channel.exchange_declare(exchange=exchange, exchange_type="direct")

        channel.basic_publish(exchange=exchange, routing_key=routing_key, body=message)

    return {"sent": message}


@router.post("/topic")
def send_message_to_specific_subscribers(
    exchange: str = "topic_logs",
    message: str = "Log 1",
    routing_key: str = "kern.critical",
):
    """Send message to a topic exchange on RabbitMQ"""

    parameters = pika.ConnectionParameters(host=env["RABBITMQ_HOST"], port=env["RABBITMQ_PORT"],
                                           credentials=rmq_credentials,virtual_host=env["RABBITMQ_VHOST"])

    with pika.BlockingConnection(parameters) as connection:
        channel = connection.channel()

        channel.exchange_declare(exchange=exchange, exchange_type="topic")

        channel.basic_publish(exchange=exchange, routing_key=routing_key, body=message)

    return {"sent": message}


@router.post("/rpc")
def send_rpc_request(
    value: int = 30,
):
    """Send RPC request on RabbitMQ"""

    fibonacci_rpc = FibonacciRpcClient()
    response = fibonacci_rpc.call(value)

    return {"sent": value, "received": response}

class StompBody(BaseModel):
    topic: str
    message:str
    vhost:str | bool = False
@router.post("/stomp")
def send_rpc_request(
        body: StompBody
):
    if body.vhost:
        print(f"{body.topic} - {body.message} - {body.vhost}")
        conn = stomp.Connection(host_and_ports=[(env['RABBITMQ_HOST'],61613)],vhost=body.vhost)
        conn.connect(env["RABBITMQ_USER"], env["RABBITMQ_PASS"], wait=True)
        result = conn.send(body=body.message, destination=f"/{body.topic}")
        conn.disconnect()
        return {"sent": body.message, "result": result}
    return {"error": "Please input the 'vhost' value in params."}
