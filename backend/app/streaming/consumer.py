import json
import logging
from kafka import KafkaConsumer, KafkaProducer
from app.ml.anomaly import detect_anomalies_streaming

logger = logging.getLogger(__name__)

def run_realtime_inference():
    '''
    Kafka Consumer running as a distributed worker.
    Ingests live sales data, runs inference in memory, and pushes anomalies to an alert topic.
    '''
    consumer = KafkaConsumer(
        'live-sales-events',
        bootstrap_servers=['kafka-cluster.streaming.svc.cluster.local:9092'],
        group_id='ml-inference-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    producer = KafkaProducer(
        bootstrap_servers=['kafka-cluster.streaming.svc.cluster.local:9092'],
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )

    logger.info("Started Distributed Streaming Inference Engine...")
    
    for message in consumer:
        event = message.value
        tenant_id = event.get('tenant_id')
        
        # Real-time inference
        is_anomalous, severity = detect_anomalies_streaming(event)
        
        if is_anomalous:
            alert = {
                "tenant_id": tenant_id,
                "sku": event.get('sku'),
                "severity": severity,
                "timestamp": event.get('timestamp')
            }
            producer.send('anomaly-alerts', value=alert)
            logger.warning(f"Real-time Anomaly Detected for Tenant {tenant_id}: {alert}")
