from fastapi import FastAPI
from src.model_selection.api.routes.analyze import router as analyze_router
from src.model_selection.api.routes.health import router as health_router
from src.model_selection.api.routes.recommend import router as recommend_router
from src.model_selection.api.routes.semantic import router as semantic_router
from src.model_selection.api.routes.semantic_rerank import router as semantic_rerank_router
from src.shared.config.settings import settings
from src.shared.utils.logger import get_logger


logger = get_logger(__name__)

app = FastAPI(
    title="Model Selection API",
    version="1.0.0",
)


@app.on_event("startup")
def startup_event():
    logger.info(
        "Starting Model Selection API",
        env=settings.MONGODB_URI
    )


app.include_router(health_router)
app.include_router(analyze_router)
app.include_router(recommend_router)
app.include_router(semantic_router)
app.include_router(semantic_rerank_router)
