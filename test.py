from fastapi import FastAPI
from mangum import Mangum
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

from app.api.v1.endpoints import api_v1_router
from app.core.app_settings import app_settings
from app.core.lifespan_config import lifespan
from app.core.middleware_config import setup_middlewares
from app.core.openapi_config import custom_openapi
from app.graphql.context import graphql_context
from app.graphql.schema import schema

app = FastAPI(
    title=app_settings.APP_NAME,
    version=app_settings.VERSION,
    debug=app_settings.DEBUG,
    openapi_url=f"{app_settings.API_V1_PATH}/openapi.json",
    lifespan=lifespan,
)

app.openapi = lambda: custom_openapi(app)

setup_middlewares(app)


@app.get("/", tags=["health"])
async def health_check():
    """
    Check the health of the application.

    Returns:
        dict: The health status of the application.
    """
    return {"status": "ok"}


app.include_router(api_v1_router, prefix=app_settings.API_V1_PATH)


if app_settings.ENABLE_GRAPHQL:
    graphql_app = GraphQLRouter(
        schema,
        context_getter=graphql_context,
        graphql_ide="graphiql" if app_settings.DEBUG else None,
        subscription_protocols=[
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
        ],
    )

    app.include_router(graphql_app, prefix="/graphql")

# Mangum handler for AWS Lambda integration
# FastAPI is an ASGI framework, which is not natively supported by AWS Lambda.
# Mangum acts as a bridge, allowing the FastAPI application to run seamlessly in a serverless environment.
# This handler wraps our FastAPI app, enabling it to respond to Lambda events and handle HTTP requests.
handler = Mangum(app)
