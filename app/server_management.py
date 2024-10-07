from fastapi import APIRouter, HTTPException, Depends
from kubernetes import client, config
import random
import string
from sqlalchemy.orm import Session
from .db import get_db
from .auth import get_current_user
from .models import Payment
from .plans import plans

# Load Kubernetes configuration
config.load_kube_config(config_file="/home/sysadmin/.kube/config")

# Kubernetes API clients
apps_v1 = client.AppsV1Api()
core_v1 = client.CoreV1Api()

# Namespace to deploy into
namespace = 'default'

# Starting base NodePort
BASE_PORT = 30000

router = APIRouter()

# Get the next available NodePort
def get_next_available_port():
    MAX_PORT = 32767
    services = core_v1.list_service_for_all_namespaces()
    used_ports = set()
    for svc in services.items:
        if svc.spec.ports:
            for port in svc.spec.ports:
                if port.node_port:
                    used_ports.add(port.node_port)
    next_port = BASE_PORT
    while next_port <= MAX_PORT:
        if next_port not in used_ports:
            return next_port
        next_port += 1
    raise HTTPException(status_code=500, detail="No available NodePorts in the range 30000-32767")

@router.post("/create/")
async def create_minecraft_server(name: str, plan_id: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    # Check if the user has an active payment for the selected plan
    payment = db.query(Payment).filter(Payment.user_id == current_user.id, Payment.plan_id == plan_id, Payment.payment_status == 'paid').first()
    if not payment:
        raise HTTPException(status_code=402, detail="Payment required before creating a server.")

    try:
        # Generate a random name for the Minecraft server deployment
        deployment_name = 'minecraft-server-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        node_port = get_next_available_port()

        # Set the amount of memory based on the selected plan
        plan = plans.get(plan_id)
        if not plan:
            raise HTTPException(status_code=400, detail="Invalid plan selected.")
        memory_limit = plan['ram']

        # Create a Kubernetes deployment for the Minecraft server
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(name=deployment_name),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector={'matchLabels': {'app': 'minecraft', 'instance': deployment_name}},
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={'app': 'minecraft', 'instance': deployment_name}),
                    spec=client.V1PodSpec(containers=[
                        client.V1Container(
                            name='minecraft',
                            image='itzg/minecraft-server',
                            ports=[client.V1ContainerPort(container_port=25565)],
                            env=[client.V1EnvVar(name='EULA', value='TRUE')],
                            resources=client.V1ResourceRequirements(
                                requests={'memory': f'{memory_limit}Gi'},
                                limits={'memory': f'{memory_limit}Gi'}
                            )
                        )
                    ])
                )
            )
        )
        apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)

        # Create a service for the Minecraft server
        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=deployment_name, labels={'app': 'minecraft', 'instance': deployment_name}),
            spec=client.V1ServiceSpec(
                selector={'app': 'minecraft', 'instance': deployment_name},
                ports=[client.V1ServicePort(port=25565, target_port=25565, node_port=node_port)],
                type='NodePort'
            )
        )
        core_v1.create_namespaced_service(namespace=namespace, body=service)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    return {"message": f"Server {deployment_name} created successfully with NodePort {node_port}"}

@router.post("/delete/{deployment_name}")
async def delete_minecraft_server(deployment_name: str):
    try:
        apps_v1.delete_namespaced_deployment(name=deployment_name, namespace=namespace)
        core_v1.delete_namespaced_service(name=deployment_name, namespace=namespace)
    except client.exceptions.ApiException as e:
        raise HTTPException(status_code=e.status, detail=f"Error deleting server: {e}")

    return {"message": f"Server {deployment_name} deleted successfully"}

