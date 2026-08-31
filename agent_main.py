from __future__ import annotations

"""Foundry hosted-agent entry point — serves the handoff workflow over the
Responses protocol. The FastAPI app in src/main.py remains the local dev host."""

from dotenv import load_dotenv

load_dotenv()

# Observability must be configured before any agents or AF clients are created
from src.observability import setup_observability

setup_observability()

from agent_framework._workflows._agent import WorkflowAgent
from agent_framework_foundry_hosting import ResponsesHostServer

from src.agents.host_agent import HostAgent
from src.config import get_settings
from src.database import Base, engine, ensure_tables


class RestaurantHostAgent(WorkflowAgent):
    """Rebuilds the wrapped workflow only when the hosting layer isn't resuming
    a checkpoint, keeping unrelated conversations from leaking state into each other.

    The hosting server keys checkpoints by conversation/previous_response_id and
    always issues a restore-only call (checkpoint_id set) before the real turn for
    an existing conversation. A brand-new conversation skips that restore step
    entirely. WorkflowAgent's status, however, is one mutable attribute shared by
    every caller of this single instance — so a never-fulfilled pending handoff
    from conversation A would otherwise be inherited by a fresh conversation B that
    never checkpointed anything. Rebuilding fresh whenever a restore isn't about to
    replay real state (and right before that restore, so it replays into a clean
    workflow) keeps each conversation's state isolated. Not thread-safe for
    concurrent conversations on this instance — a future fix would key a workflow
    per conversation id instead of relying on a single shared one.
    """

    def __init__(self, host: HostAgent, **kwargs) -> None:
        self._host = host
        self._restoring = False
        super().__init__(host.build_workflow(), **kwargs)

    def run(self, messages=None, *, checkpoint_id=None, **kwargs):
        if checkpoint_id is not None:
            self._workflow = self._host.build_workflow()
            self._restoring = True
        elif not self._restoring:
            self._workflow = self._host.build_workflow()
        else:
            self._restoring = False
        return super().run(messages, checkpoint_id=checkpoint_id, **kwargs)


def main() -> None:
    settings = get_settings()
    if settings.use_table_storage():
        ensure_tables(settings.table_storage_connection_string)
    else:
        Base.metadata.create_all(bind=engine)

    agent = RestaurantHostAgent(HostAgent(), name="restaurant-host-agent")
    ResponsesHostServer(agent).run()


if __name__ == "__main__":
    main()
