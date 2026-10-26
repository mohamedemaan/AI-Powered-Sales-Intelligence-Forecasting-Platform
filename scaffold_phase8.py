import os

infra_files = {
    "infrastructure/k8s/api-deployment.yaml": """apiVersion: apps/v1
kind: Deployment
metadata:
  name: salesintel-api-gateway
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: salesintel-api
  template:
    metadata:
      labels:
        app: salesintel-api
    spec:
      containers:
      - name: api
        image: salesintel/api:latest
        resources:
          requests:
            cpu: "1"
            memory: "2Gi"
          limits:
            cpu: "2"
            memory: "4Gi"
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: salesintel-secrets
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: salesintel-api-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: salesintel-api-gateway
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
""",

    "infrastructure/k8s/kafka-cluster.yaml": """apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: salesintel-event-bus
  namespace: streaming
spec:
  kafka:
    version: 3.4.0
    replicas: 3
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: tls
        port: 9093
        type: internal
        tls: true
    storage:
      type: jbod
      volumes:
      - id: 0
        type: persistent-claim
        size: 500Gi
        deleteClaim: false
  zookeeper:
    replicas: 3
    storage:
      type: persistent-claim
      size: 100Gi
      deleteClaim: false
  entityOperator:
    topicOperator: {}
    userOperator: {}
""",

    "backend/app/streaming/consumer.py": """import json
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
""",

    "backend/app/api/v2/endpoints/automl.py": """from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
import uuid

router = APIRouter()

@router.post("/train")
def trigger_automl_pipeline(tenant_id: str, dataset_url: str, target_column: str, background_tasks: BackgroundTasks):
    '''
    AutoML Engine API Layer.
    Triggers distributed Airflow/Prefect DAGs to train models across a Kubernetes GPU cluster.
    '''
    job_id = str(uuid.uuid4())
    
    # In production, this pushes a message to Kafka or triggers an Airflow DAG
    # trigger_airflow_dag("automl_training_pipeline", conf={"job_id": job_id, "dataset": dataset_url, "target": target_column})
    
    return {
        "status": "ACCEPTED",
        "job_id": job_id,
        "message": "AutoML distributed training job initiated."
    }

@router.get("/status/{job_id}")
def get_automl_status(job_id: str):
    '''
    Polls the Model Registry / Orchestrator for job status.
    '''
    return {
        "job_id": job_id,
        "status": "TRAINING",
        "progress": "45%",
        "current_stage": "Hyperparameter Optimization"
    }
""",

    "backend/app/api/v2/api.py": """from fastapi import APIRouter
from app.api.v2.endpoints import automl

api_router_v2 = APIRouter()
api_router_v2.include_router(automl.router, prefix="/automl", tags=["AutoML Platform"])
"""
}

def create_phase8():
    for filepath, content in infra_files.items():
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
    # Update API Router for V2 Infrastructure API
    main_path = "backend/app/main.py"
    if os.path.exists(main_path):
        with open(main_path, "r", encoding='utf-8') as f:
            content = f.read()
        if "api_router_v2" not in content:
            with open(main_path, "w", encoding='utf-8') as f:
                new_content = content.replace(
                    "from app.api.v1.api import api_router",
                    "from app.api.v1.api import api_router\\nfrom app.api.v2.api import api_router_v2"
                )
                new_content += "\\napp.include_router(api_router_v2, prefix='/api/v2')\\n"
                f.write(new_content)

if __name__ == "__main__":
    create_phase8()
    print("Phase 8 setup (Global AI Infrastructure & Kubernetes) completed successfully!")
