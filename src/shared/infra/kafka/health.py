from aiokafka.errors import KafkaError

from src.shared.infra.kafka.producer import KafkaEventProducer


async def check_kafka_connection(
    *,
    bootstrap_servers: str,
    client_id: str,
) -> bool:
    producer = KafkaEventProducer(
        bootstrap_servers=bootstrap_servers,
        client_id=client_id,
    )

    try:
        await producer.start()
        return True
    except (KafkaError, OSError, TimeoutError):
        return False
    finally:
        await producer.stop()
