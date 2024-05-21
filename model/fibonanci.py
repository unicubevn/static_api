import pika
import uuid

from dotenv import dotenv_values

env = dotenv_values(".env")
rmq_credentials = pika.PlainCredentials(env["RABBITMQ_USER"], env["RABBITMQ_PASS"])


class FibonacciRpcClient(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=env["RABBITMQ_HOST"], port=env["RABBITMQ_PORT"],
                                      credentials=rmq_credentials, virtual_host=env["RABBITMQ_VHOST"])
        )

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue="", exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True,
        )

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())

        self.channel.basic_publish(
            exchange="",
            routing_key="rpc_queue",
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=str(n),
        )

        while self.response is None:
            self.connection.process_data_events()

        self.connection.close()

        return int(self.response)
