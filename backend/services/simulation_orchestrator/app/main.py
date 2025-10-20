from fastapi import FastAPI, BackgroundTasks
import logging
import docker
import os

# config logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# config FASTAPI
app = FastAPI(
    title="AxleOS - Simulation Orchestrator",
    description="An API to manage and trigger vehicle simulations.",
    version="0.1.0"
)

def run_simulation_container():

    try:
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        client.ping()

        beamng_path_on_host = os.getenv("BEAMNG_HOST_PATH")
        if not beamng_path_on_host:
            logger.error("BEAMNG_HOST_PATH environment variable is not set!")
            return

        logger.info(f"Host path for BeamNG found: {beamng_path_on_host}")
        logger.info("Starting a new simulation container with volume mount...")

        container = client.containers.run(
            "simulator:latest",
            detach=True,
            network="infrastructure_default",
            volumes={
                beamng_path_on_host: {
                    'bind': '/app/BeamNG.tech', 
                    'mode': 'ro'
                }
            },
            environment={
                "MINIO_ENDPOINT": "http://minio:9000",
                "RABBITMQ_HOST": "rabbitmq"
            }
        )
        logger.info(f"Started container {container.short_id}")
    except Exception as e:
        logger.error(f"Failed to start simulation container: {e}")
    

@app.post("/simulations", status_code=202)
def create_simulation(background_tasks: BackgroundTasks):
    #creates a simulation by using docker
    logger.info("Received request to start a new simulation.")
    background_tasks.add_task(run_simulation_container)
    return {"message": "Simulation run has been triggered in the background."}


# Simple health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}