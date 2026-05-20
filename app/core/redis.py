import pickle
import asyncio
from typing import Any, AsyncIterator, Dict, Iterator, Optional
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
)
import redis
from app.core.config import settings

class RedisCheckpointSaver(BaseCheckpointSaver):
    """Custom, high-reliability LangGraph Checkpoint Saver using Redis.
    
    Persists agent conversation context dynamically across turns linked to user session IDs.
    Implements both sync and async interfaces required by LangGraph.
    """
    def __init__(self, host: str, port: int, db: int = 0):
        super().__init__()
        self.client = redis.Redis(host=host, port=port, db=db)

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Fetch a specific or latest checkpoint tuple for the current thread."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id")
        
        # 1. Fetch exact checkpoint if checkpoint_id is supplied
        if checkpoint_id:
            key = f"checkpoint:{thread_id}:{checkpoint_id}"
            data = self.client.get(key)
            if data:
                chk_dict = pickle.loads(data)
                return CheckpointTuple(
                    config=config,
                    checkpoint=chk_dict["checkpoint"],
                    metadata=chk_dict["metadata"],
                    parent_config=chk_dict.get("parent_config"),
                )
            return None
            
        # 2. Otherwise, fetch latest checkpoint for this conversation thread
        keys = self.client.keys(f"checkpoint:{thread_id}:*")
        if not keys:
            return None
            
        checkpoints = []
        for k in keys:
            data = self.client.get(k)
            if data:
                chk_dict = pickle.loads(data)
                checkpoints.append((chk_dict, k))
                
        if not checkpoints:
            return None
            
        # Sort by internal timestamp to locate the most recent state
        checkpoints.sort(key=lambda x: x[0]["checkpoint"]["ts"], reverse=True)
        latest_chk_dict, latest_key = checkpoints[0]
        
        latest_checkpoint_id = latest_key.decode("utf-8").split(":")[-1]
        
        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": latest_checkpoint_id,
                }
            },
            checkpoint=latest_chk_dict["checkpoint"],
            metadata=latest_chk_dict["metadata"],
            parent_config=latest_chk_dict.get("parent_config"),
        )

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Async wrapper for get_tuple — runs sync Redis I/O in a thread executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_tuple, config)

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Persist a conversation state checkpoint to Redis."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint["id"]
        
        parent_checkpoint_id = config["configurable"].get("checkpoint_id")
        parent_config = None
        if parent_checkpoint_id:
            parent_config = {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": parent_checkpoint_id,
                }
            }
            
        key = f"checkpoint:{thread_id}:{checkpoint_id}"
        
        checkpoint_dict = {
            "checkpoint": checkpoint,
            "metadata": metadata,
            "new_versions": new_versions,
            "parent_config": parent_config,
        }
        
        # Store state using robust pickle serialization (needed to support complex LangGraph states)
        self.client.set(key, pickle.dumps(checkpoint_dict))
        
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
            }
        }

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Async wrapper for put — runs sync Redis I/O in a thread executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.put, config, checkpoint, metadata, new_versions
        )

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Any,
        task_id: str,
    ) -> None:
        """Persist intermediate channel writes for a checkpoint task to Redis."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id", "")
        key = f"writes:{thread_id}:{checkpoint_id}:{task_id}"
        self.client.set(key, pickle.dumps(writes))

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Any,
        task_id: str,
    ) -> None:
        """Async wrapper for put_writes — runs sync Redis I/O in a thread executor."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, self.put_writes, config, writes, task_id
        )

    def list(
        self,
        config: RunnableConfig,
        *,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """Yield historical checkpoints for the thread, matching before/limit constraints."""
        thread_id = config["configurable"]["thread_id"]
        keys = self.client.keys(f"checkpoint:{thread_id}:*")
        
        checkpoints = []
        for k in keys:
            data = self.client.get(k)
            if data:
                chk_dict = pickle.loads(data)
                checkpoint_id = k.decode("utf-8").split(":")[-1]
                checkpoints.append((chk_dict, checkpoint_id))
                
        checkpoints.sort(key=lambda x: x[0]["checkpoint"]["ts"], reverse=True)
        
        if before:
            before_id = before["configurable"].get("checkpoint_id")
            found_idx = -1
            for idx, (_, chk_id) in enumerate(checkpoints):
                if chk_id == before_id:
                    found_idx = idx
                    break
            if found_idx != -1:
                checkpoints = checkpoints[found_idx + 1:]
                
        if limit:
            checkpoints = checkpoints[:limit]
            
        for chk_dict, chk_id in checkpoints:
            yield CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_id": chk_id,
                    }
                },
                checkpoint=chk_dict["checkpoint"],
                metadata=chk_dict["metadata"],
                parent_config=chk_dict.get("parent_config"),
            )

    async def alist(
        self,
        config: RunnableConfig,
        *,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """Async wrapper for list — collects sync results in executor then yields them."""
        loop = asyncio.get_event_loop()
        # Collect all results from the sync iterator in a thread
        results = await loop.run_in_executor(
            None, lambda: list(self.list(config, before=before, limit=limit))
        )
        for item in results:
            yield item

def get_redis_checkpointer() -> RedisCheckpointSaver:
    """FastAPI Dependency yielding the RedisCheckpointSaver instance."""
    return RedisCheckpointSaver(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

