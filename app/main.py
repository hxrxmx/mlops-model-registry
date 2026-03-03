from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Float

from app.db import get_db, engine, Base
from app import models, schemas


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Model registry API", lifespan=lifespan)


@app.post("/register", response_model=schemas.ModelVersionOut)
async def register_model(
    data: schemas.ModelRegister,
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(
        select(models.Model).where(models.Model.name == data.model_name)
    )
    model = result.scalars().first()

    if not model:
        model = models.Model(
            name=data.model_name, team=data.team, description=data.description
        )
        db.add(model)
        await db.flush()

    version_result = await db.execute(
        select(func.max(models.ModelVersion.version_number))
        .where(models.ModelVersion.model_id == model.id)
    )
    last_version = version_result.scalar() or 0
    new_version_number = last_version + 1

    new_version = models.ModelVersion(
        model_id=model.id,
        version_number=new_version_number,
        dvc_hash=data.dvc_hash,
        config=data.config,
        metrics=data.metrics,
        status=models.ModelStatus.STAGING
    )

    db.add(new_version)
    await db.commit()
    await db.refresh(new_version)

    return new_version


@app.get("/models/{name}/latest", response_model=schemas.ModelVersionOut)
async def get_latest(name: str, db: AsyncSession = Depends(get_db)):
    query = (
        select(models.ModelVersion).join(models.Model)
        .where(models.Model.name == name)
        .order_by(models.ModelVersion.version_number.desc())
        .limit(1)
    )

    res = await db.execute(query)
    latest = res.scalars().first()

    if not latest:
        raise HTTPException(404, "model not found")
    return latest


@app.get("/models/{name}/best", response_model=schemas.ModelVersionOut)
async def get_best(
    name: str,
    metric: str = "accuracy",
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(models.ModelVersion).join(models.Model)
        .where(models.Model.name == name)
        .order_by(
            cast(
                models.ModelVersion.metrics[metric].as_string(),
                Float
            ).desc()
        ).limit(1)
    )
    res = await db.execute(query)
    best = res.scalars().first()

    if not best:
        raise HTTPException(404, "Model or metric not found")
    return best


@app.patch("/versions/{id}/status", response_model=schemas.ModelVersionOut)
async def set_status(
    id: int,
    status: models.ModelStatus,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(models.ModelVersion)
        .where(models.ModelVersion.id == id)
    )

    v = res.scalars().first()
    if not v:
        raise HTTPException(404, f"id {id} not found")
    v.status = status
    await db.commit()
    await db.refresh(v)
    return v
