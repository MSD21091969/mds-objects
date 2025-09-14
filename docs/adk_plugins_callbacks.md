# ADK Plugin Callback Patterns for Monitoring

The Google Agent Development Kit (ADK) provides a powerful plugin system that allows developers to inject custom logic at various points in an agent's lifecycle. These "callbacks" are invaluable for implementing comprehensive monitoring, logging, and management solutions.

This document outlines the key callback methods available in ADK plugins, their purpose, when they are triggered, and the information they provide.

## BasePlugin Lifecycle Methods

All custom ADK plugins should inherit from `google.adk.plugins.BasePlugin`. This base class defines a set of asynchronous methods that can be overridden to implement custom logic.

### 1. Run Lifecycle Callbacks

These callbacks are triggered at the beginning, end, or during an error in an agent's overall execution run.

*   **`async def on_run_start(self, session: Session, agent: Agent, **kwargs: Any) -> None`**
    *   **Purpose:** Called at the very beginning of an agent's run.
    *   **Triggered:** Before any events are processed or tools are called for a given `runner.run_async` invocation.
    *   **Information Provided:**
        *   `session`: The current `Session` object, containing `session_id`, `user_id`, `app_name`, and the current state.
        *   `agent`: The `Agent` instance being run.
        *   `kwargs`: Additional keyword arguments passed to `runner.run_async`.
    *   **Monitoring Use Cases:**
        *   Start a new OpenTelemetry trace span for the entire agent run.
        *   Log the start of an agent's execution.
        *   Initialize run-specific metrics or context.

*   **`async def on_run_end(self, session: Session, agent: Agent, **kwargs: Any) -> None`**
    *   **Purpose:** Called at the successful completion of an agent's run.
    *   **Triggered:** After all events have been processed and the agent has produced a final response (or completed its task) without errors.
    *   **Information Provided:**
        *   `session`: The final `Session` object.
        *   `agent`: The `Agent` instance that completed the run.
        *   `kwargs`: Additional keyword arguments.
    *   **Monitoring Use Cases:**
        *   End the OpenTelemetry trace span started in `on_run_start`.
        *   Log the successful completion of an agent's execution.
        *   Record final run metrics (e.g., duration, number of events processed).

*   **`async def on_run_error(self, session: Session, agent: Agent, error: Exception, **kwargs: Any) -> None`**
    *   **Purpose:** Called when an unhandled exception occurs during an agent's run.
    *   **Triggered:** Whenever an exception is raised and not caught within the agent's execution flow.
    *   **Information Provided:**
        *   `session`: The `Session` object at the time of the error.
        *   `agent`: The `Agent` instance that encountered the error.
        *   `error`: The `Exception` object that was raised.
        *   `kwargs`: Additional keyword arguments.
    *   **Monitoring Use Cases:**
        *   Mark the OpenTelemetry trace span as an error and record the exception.
        *   Log detailed error information, including stack traces.
        *   Trigger alerts for critical failures.

### 2. Event Processing Callbacks

These callbacks are triggered as the ADK Runner processes individual events within a session.

*   **`async def on_event(self, session: Session, event: Event, **kwargs: Any) -> None`**
    *   **Purpose:** Called every time the ADK Runner processes an `Event` object.
    *   **Triggered:** For each `Event` yielded by the agent during its `run_async` execution. This includes user messages, agent responses, tool calls, tool results, and internal state changes.
    *   **Information Provided:**
        *   `session`: The current `Session` object.
        *   `event`: The `Event` object being processed. This object contains `type`, `timestamp`, and `content` (which can vary based on event type).
        *   `kwargs`: Additional keyword arguments.
    *   **Monitoring Use Cases:**
        *   Create child OpenTelemetry spans for each event to visualize the agent's thought process.
        *   Log specific event types (e.g., user input, agent output, tool invocation details).
        *   Extract and record metrics related to event frequency or content.
        *   Monitor session state changes by inspecting `event.type` (e.g., if a custom event type `session_state_updated` is used).

### 3. Tool Execution Callbacks

These callbacks provide granular insight into when tools are invoked by the agent and their outcomes.

*   **`async def on_tool_start(self, session: Session, agent: Agent, tool: FunctionTool, **kwargs: Any) -> None`**
    *   **Purpose:** Called just before an agent invokes a `FunctionTool`.
    *   **Triggered:** When the agent decides to call a tool based on its reasoning.
    *   **Information Provided:**
        *   `session`: The current `Session` object.
        *   `agent`: The `Agent` instance invoking the tool.
        *   `tool`: The `FunctionTool` object being invoked.
        *   `kwargs`: Contains `tool_args` (the arguments passed to the tool).
    *   **Monitoring Use Cases:**
        *   Start a child OpenTelemetry span for the tool invocation.
        *   Log the tool name and its arguments.
        *   Monitor tool usage patterns and frequency.

*   **`async def on_tool_end(self, session: Session, agent: Agent, tool: FunctionTool, result: Any, **kwargs: Any) -> None`**
    *   **Purpose:** Called after a `FunctionTool` has successfully executed.
    *   **Triggered:** When the tool returns a result without raising an exception.
    *   **Information Provided:**
        *   `session`: The current `Session` object.
        *   `agent`: The `Agent` instance that invoked the tool.
        *   `tool`: The `FunctionTool` object that completed.
        *   `result`: The return value of the tool execution.
        *   `kwargs`: Additional keyword arguments.
    *   **Monitoring Use Cases:**
        *   End the OpenTelemetry span for the tool invocation.
        *   Log the tool's result.
        *   Record tool execution duration and success rates.

*   **`async def on_tool_error(self, session: Session, agent: Agent, tool: FunctionTool, error: Exception, **kwargs: Any) -> None`**
    *   **Purpose:** Called when a `FunctionTool` invocation raises an exception.
    *   **Triggered:** When an error occurs during the execution of a tool.
    *   **Information Provided:**
        *   `session`: The current `Session` object.
        *   `agent`: The `Agent` instance that invoked the tool.
        *   `tool`: The `FunctionTool` object that failed.
        *   `error`: The `Exception` object that was raised by the tool.
        *   `kwargs`: Additional keyword arguments.
    *   **Monitoring Use Cases:**
        *   Mark the OpenTelemetry span for the tool invocation as an error and record the exception.
        *   Log detailed error information for tool failures.
        *   Monitor tool error rates and identify problematic tools.

## Structuring Code Exposing All Possible Implementations

To fully leverage these callbacks, your `LoggingPlugin` and `OpenTelemetryMonitoringPlugin` should implement as many of these methods as are relevant to your monitoring needs. The examples provided in `src/core/adk_monitoring/plugins/logging_plugin.py` and `src/core/adk_monitoring/plugins/opentelemetry_plugin.py` demonstrate how to implement a subset of these.

For a comprehensive monitoring solution, consider:

*   **`ADKMonitoringService`:** This service acts as the central dispatcher for all monitoring data collected by the plugins. It can then decide where to log, store, or process this data (e.g., to standard logs, a database, Pub/Sub, or a metrics system).
*   **Custom Event Types:** The ADK `Event` object is flexible. You can define custom event types within your agent or tools to signal specific internal state changes or significant actions that you want to monitor via the `on_event` callback.
*   **Contextual Information:** Always ensure that relevant contextual information (like `session_id`, `user_id`, `agent_name`, `casefile_id` if available in the session state) is included in your logs and trace spans to enable effective filtering and analysis in your monitoring tools.

By systematically implementing these callbacks and integrating them with your `ADKMonitoringService` and OpenTelemetry setup, you can build a powerful and granular monitoring system for your ADK-powered application.
