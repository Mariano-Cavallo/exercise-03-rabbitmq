import os
import json
import pika
import sys

def main():
    # Retrieve RabbitMQ connection URL from environment variables
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
    
    try:
        # Establish connection and channel
        parameters = pika.URLParameters(rabbitmq_url)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Ensure the queue exists and is durable
        channel.queue_declare(queue='node_events', durable=True)

        def callback(ch, method, properties, body):
            try:
                # Parse the JSON message payload
                data = json.loads(body)
                event = data.get("event")
                node_name = data.get("node_name")
                timestamp = data.get("timestamp")

                # Log to stdout in the specified format
                print(f"EVENT: {event} | node: {node_name} | time: {timestamp}")
                sys.stdout.flush()

                # Acknowledge successful processing
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"Error processing message: {e}")

        # Set QoS to ensure fair dispatch among multiple consumers
        channel.basic_qos(prefetch_count=1)
        
        # Configure consumer
        channel.basic_consume(queue='node_events', on_message_callback=callback)

        print(" [*] Waiting for messages in 'node_events'. To exit press CTRL+C")
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as e:
        print(f"Could not connect to RabbitMQ: {e}")
    except KeyboardInterrupt:
        print("\nConsumer stopped.")
        try:
            connection.close()
        except:
            pass

if __name__ == "__main__":
    main()