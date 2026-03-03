from fastapi import APIRouter
from strawberry.fastapi import GraphQLRouter

from src.app.api.v1.graphql import build_schema

router = APIRouter()
router.include_router(router=GraphQLRouter(schema=build_schema()), prefix="/graphql")
