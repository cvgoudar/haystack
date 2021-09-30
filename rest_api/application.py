import logging

from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

from haystack import Pipeline
from rest_api.config import PIPELINE_YAML_PATH, QUERY_PIPELINE_NAME
from rest_api.controller.errors.http_error import http_error_handler
from rest_api.config import ROOT_PATH


logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)
logging.getLogger("elasticsearch").setLevel(logging.WARNING)
logging.getLogger("haystack").setLevel(logging.INFO)


PIPELINE = Pipeline.load_from_yaml(Path(PIPELINE_YAML_PATH), pipeline_name=QUERY_PIPELINE_NAME)
# TODO make this generic for other pipelines with different naming
RETRIEVER = PIPELINE.get_node(name="Retriever")
DOCUMENT_STORE = RETRIEVER.document_store if RETRIEVER else None
logging.info(f"Loaded pipeline nodes: {PIPELINE.graph.nodes.keys()}")


from rest_api.controller.router import router as api_router


def get_application() -> FastAPI:
    application = FastAPI(title="Haystack-API", debug=True, version="0.1", root_path=ROOT_PATH)

    # This middleware enables allow all cross-domain requests to the API from a browser. For production
    # deployments, it could be made more restrictive.
    application.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
    )

    application.add_exception_handler(HTTPException, http_error_handler)

    application.include_router(api_router)

    return application


app = get_application()


logger.info("Open http://127.0.0.1:8000/docs to see Swagger API Documentation.")
logger.info(
    """
    Or just try it out directly: curl --request POST --url 'http://127.0.0.1:8000/query' -H "Content-Type: application/json"  --data '{"query": "Did Albus Dumbledore die?"}'
    """
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
