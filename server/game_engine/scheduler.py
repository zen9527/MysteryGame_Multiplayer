import asyncio
import logging
from datetime import datetime

log = logging.getLogger(__name__)


class GameScheduler:
    """Periodic monitor that triggers autonomous DM behavior."""

    def __init__(self, game_host, game_manager, ws_hub):
        self._host = game_host
        self._manager = game_manager
        self._hub = ws_hub
        self._tasks: dict[str, asyncio.Task] = {}

    def start(self, game_id: str):
        if game_id in self._tasks:
            return
        self._tasks[game_id] = asyncio.create_task(self._monitor_loop(game_id))
        log.info(f"[Scheduler] Started monitoring game {game_id}")

    def stop(self, game_id: str):
        task = self._tasks.pop(game_id, None)
        if task:
            task.cancel()
            log.info(f"[Scheduler] Stopped monitoring game {game_id}")

    def stop_all(self):
        for game_id in list(self._tasks.keys()):
            self.stop(game_id)

    async def _monitor_loop(self, game_id: str):
        try:
            while True:
                await asyncio.sleep(30)
                state = self._manager.get_state(game_id)
                if not state or state.phase in ("revealed", "finished"):
                    break
                if self._host.should_intervene(state):
                    await self._do_intervention(game_id, state)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error(f"[Scheduler] Error monitoring {game_id}: {e}")
        finally:
            self._tasks.pop(game_id, None)

    async def _do_intervention(self, game_id: str, state):
        try:
            event = await asyncio.wait_for(
                asyncio.to_thread(self._host.generate_idle_nudge, state),
                timeout=60,
            )
            result = self._manager.push_structured_event(game_id, event)
            if result and result["public_event"]:
                await self._hub.broadcast(game_id, {
                    "type": "event",
                    "content": result["public_event"],
                })
                for clue in result["private_clues"]:
                    await self._hub.send_dm_private(game_id, clue["player_id"], clue["content"])

            state.dm_intervention_history.append({
                "type": "idle_nudge",
                "timestamp": datetime.now().isoformat(),
                "event": event.get("public_event", "")[:100],
            })
            state.last_player_activity = datetime.now()
        except asyncio.TimeoutError:
            self._manager.add_dm_log(game_id, "自动干预超时（60s）")
        except Exception as e:
            self._manager.add_dm_log(game_id, f"自动干预失败: {e}")
