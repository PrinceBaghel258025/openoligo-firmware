"""
Script to start the REST API server for OpenOligo.
"""
import logging
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, status
from tortoise import Tortoise
from tortoise.exceptions import ValidationError

from openoligo.api.models import (
    SynthesisQueue,
    TaskQueueInModel,
    TaskQueueModel,
    TaskStatus,
    ValidSeq,
)
from openoligo.hal.platform import Platform, __platform__
from openoligo.seq import SeqCategory

DESCRIPTION = """
OpenOligo API for the synthesis of oligonucleotides.

You can
* Request a new oligo synthesis task.
* Check the status of the sequences waiting to be synthesized.
* Read and Update the configuration and the staus of the instrument.

## SynthesisQueue

You will be able to:

* **Add a Sequence** to the Synthesis Queue.
* **Update the sequence and order of synthesis**.
* **Check the status** of a Sequence in the Queue.
* **Remove a Sequence** from the Queue.

## Instrument

You will be able to:

* **Read the configuration** of the instrument (_not implemented_).
* **Update the configuration** of the instrument (_not implemented_).
* **Read the status** of the instrument (_not implemented_).
* **Update the status** of the instrument (_not implemented_).
"""


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(
    title="OpenOligo API",
    summary="REST API for OpenOligo",
    description=DESCRIPTION,
    version="0.1.6",
    contact={
        "name": "Satyam Tiwary",
        "email": "satyam@technoculture.io",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


@app.on_event("startup")
async def startup_event():
    """Startup event for the FastAPI server."""
    logging.info("Starting the API server...")

    if not __platform__:
        logging.error("Platform not supported.")
        raise RuntimeError("No platform detected")

    db_url = "sqlite://openoligo.db"
    if __platform__ in (Platform.RPI, Platform.BB):
        db_url = "sqlite:////var/log/openoligo.db"

    logging.info("Using database: '%s'", db_url)

    await Tortoise.init(db_url=db_url, modules={"models": ["openoligo.api.models"]})
    await Tortoise.generate_schemas()


@app.get("/health", status_code=200, tags=["Uitlities"])
def get_health_status():
    """Health check."""
    return {"status": "ok"}


@app.post("/queue", status_code=status.HTTP_201_CREATED, tags=["Synthesis Queue"])
async def add_a_task_to_synthesis_queue(
    sequence: str, category: SeqCategory = SeqCategory.DNA, rank: int = 0
):
    """Add a synthesis task to the synthesis task queue by providing a sequence and its category."""
    if category not in list(SeqCategory):
        raise HTTPException(status_code=400, detail="Invalid category")
    try:
        model = await SynthesisQueue.create(sequence=sequence, category=category, rank=rank)
        return model
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        logging.info("Added sequence '%s' to the synthesis queue.", sequence)


@app.get("/queue", response_model=list[TaskQueueModel], tags=["Synthesis Queue"])
async def get_all_tasks_in_synthesis_queue(filter_by: Optional[TaskStatus] = None):
    """Get the current synthesis task queue."""
    tasks = SynthesisQueue.all().order_by("-rank", "-created_at")
    if filter_by:
        tasks = tasks.filter(status=filter)
    return await tasks


@app.delete("/queue", status_code=status.HTTP_202_ACCEPTED, tags=["Synthesis Queue"])
async def clear_all_queued_tasks_in_task_queue():
    """Delete all tasks in the QUEUED state."""
    return await SynthesisQueue.filter(status=TaskStatus.QUEUED).delete()


@app.get("/queue/{task_id}", response_model=TaskQueueInModel, tags=["Synthesis Queue"])
async def get_task_by_id(task_id: int):
    """Get a synthesis task from the queue."""
    task = await SynthesisQueue.get_or_none(id=task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sythesis task not found")
    return task


@app.patch("/queue/{task_id}", status_code=status.HTTP_202_ACCEPTED, tags=["Synthesis Queue"])
async def update_a_synthesis_task(task_id: int, sequence: Optional[str] = None, rank: int = 0):
    """Update a particular task in the queue."""
    task = await SynthesisQueue.get_or_none(id=task_id)

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sequence task not found")

    if task.status != TaskStatus.QUEUED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Sequence task not in QUEUED state"
        )

    if sequence is not None:
        try:
            seq_validator = ValidSeq()
            seq_validator(sequence)
            task.sequence = sequence
        except ValidationError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if task.rank != rank:
        task.rank = rank

    await task.save()

    return task


@app.delete("/queue/{task_id}", status_code=status.HTTP_202_ACCEPTED, tags=["Synthesis Queue"])
async def delete_synthesis_task_by_id(task_id: int):
    """Delete a synthesis task from the queue."""
    task = await SynthesisQueue.get_or_none(id=task_id)

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sequence not found")

    await task.delete()

    return task


def main():
    """Main function to start the server."""
    uvicorn.run("openoligo.api.server:app", host="127.0.0.1", port=9191, reload=True)


if __name__ == "__main__":
    main()