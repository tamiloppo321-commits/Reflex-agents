import os
import json
import logging
from datetime import datetime
from openai import OpenAI

# =====================================================================
# SYSTEM INITIALIZATION & LOGGING STATE CONFIGURATION
# =====================================================================
LOG_FILENAME = "agent_incident_history.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILENAME, encoding="utf-8"),
        logging.StreamHandler()  # Still routes simple diagnostic prints directly to screen
    ]
)

def verify_environment_security() -> OpenAI:
    """Safely checks authorization profiles before initializing connection threads."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        critical_error = (
            "CRITICAL SECURITY EXCEPTION: The environment key 'OPENAI_API_KEY' is missing.\n"
            "Please check out the README.md file blueprint to configure runtime parameters properly."
        )
        logging.critical(critical_error)
        raise EnvironmentError(critical_error)
    return OpenAI(api_key=api_key)

# Initialize global authenticated client connection safely
try:
    client = verify_environment_security()
except EnvironmentError:
    # Allows module to still parse syntax without breaking system imports
    client = None

# =====================================================================
# PART 1: DEFINE THE TOOLS (BUSINESS LOGIC)
# =====================================================================

def get_server_health(server_id: str) -> str:
    """Returns CPU and Memory usage for a given server."""
    logging.info(f"Executing Tool 'get_server_health' for: {server_id}")

    metrics = {
        "payment-server-01": {"cpu": "98%", "memory": "40%", "status": "Warning"},
        "db-node-02": {"cpu": "12%", "memory": "60%", "status": "Healthy"},
        "auth-service-03": {"cpu": "45%", "memory": "95%", "status": "Critical"},
        "search-index-09": {"cpu": "10%", "memory": "15%", "status": "Error"},
        "frontend-node-04": {"cpu": "25%", "memory": "30%", "status": "Healthy"},
    }

    result = metrics.get(server_id, {"error": f"Server with ID '{server_id}' not found in asset registry."})
    return json.dumps(result)


def fetch_recent_logs(server_id: str, lines: int = 5) -> str:
    """Returns the last N lines of logs."""
    logging.info(f"Executing Tool 'fetch_recent_logs' [Lines: {lines}] for: {server_id}")

    log_database = {
        "payment-server-01": [
            "[INFO] Request received /pay/v1",
            "[WARN] CPU threshold exceeded 90%",
            "[WARN] Thread pool exhaustion",
            "[CRITICAL] Process hung, not accepting new connections",
            "[ERROR] Timeout waiting for thread"
        ],
        "db-node-02": [
            "[INFO] Backup started",
            "[INFO] Backup completed successfully",
            "[INFO] User query executed in 12ms",
            "[INFO] Health check: OK",
            "[INFO] Replication sync active"
        ],
        "auth-service-03": [
            "[INFO] Token validated user_882",
            "[WARN] Garbage collection taking too long (>5s)",
            "[ERROR] java.lang.OutOfMemoryError: Java heap space",
            "[CRITICAL] Application crashing due to memory leak",
            "[INFO] Restarting context..."
        ],
        "search-index-09": [
            "[INFO] Indexing started",
            "[ERROR] Connection refused: elastic-cluster-main:9200",
            "[ERROR] Failed to write document ID 4432",
            "[CRITICAL] Dependency Unreachable: Search Engine is down",
            "[ERROR] Retrying in 30s..."
        ],
        "frontend-node-04": [
            "[INFO] GET /home 200 OK",
            "[INFO] GET /assets/logo.png 200 OK",
            "[INFO] GET /login 200 OK",
            "[INFO] GET /api/v1/status 200 OK",
            "[INFO] Health check passed"
        ]
    }

    default_logs = ["[INFO] System stable", "[INFO] Heartbeat signal received"]
    logs = log_database.get(server_id, default_logs)
    return json.dumps({"logs": logs[:lines]})


def restart_service(server_id: str) -> str:
    """Restarts the service on the specified server."""
    logging.warning(f"AUTOMATED REMEDIATION TRIGGERED: Attempting safe reset on {server_id}...")
    result = {"status": "success", "message": f"Server {server_id} restarted successfully via hot-swap profiles."}
    return json.dumps(result)


def escalate_to_engineer(summary: str) -> str:
    """Escalates the issue to a human engineer when automated fixes fail."""
    logging.error(f"ESCALATION ROUTINE INVOKED: Routing status logs to engineering. Summary details: {summary}")
    result = {"status": "success", "message": f"PagerDuty ticket created successfully. Incident Summary payload: {summary}"}
    return json.dumps(result)


# Map functions for the agent execution loop
AVAILABLE_FUNCTIONS = {
    "get_server_health": get_server_health,
    "fetch_recent_logs": fetch_recent_logs,
    "restart_service": restart_service,
    "escalate_to_engineer": escalate_to_engineer,
}

# =====================================================================
# PART 2: DEFINE THE AGENT SCHEMA
# =====================================================================

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_server_health",
            "description": "Checks the current CPU and memory usage of a specific server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "The ID of the server, e.g., 'payment-server-01'"}
                },
                "required": ["server_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_recent_logs",
            "description": "Retrieves the most recent log entries from a server to diagnose errors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "The ID of the server."},
                    "lines": {"type": "integer", "description": "Number of log lines to fetch."}
                },
                "required": ["server_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restart_service",
            "description": "Restarts the specified server to clear resource thresholds or hung states.",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "The ID of the server to restart, e.g., 'payment-server-01'"}
                },
                "required": ["server_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_engineer",
            "description": "Escalates the issue to a human engineer when automated fixes fail or the error is unknown.",
            "parameters": {
                "type": "object",
                "properties": {
                     "summary": {"type": "string", "description": "A description summary of why the issue needs escalation."}
                },
                "required": ["summary"]
            }
        }
    }
]

# =====================================================================
# PART 3: THE AGENT EXECUTION LOOP WITH ERROR HANDLING
# =====================================================================

def run_it_agent(user_issue: str):
    logging.info(f"INITIATING TRACKING LOOP FOR INCIDENT: '{user_issue}'")
    
    if client is None:
        print("\n❌ Error: Cannot run agent because the OpenAI API Key is missing. Check 'agent_incident_history.log' for details.")
        return

    messages = [
        {"role": "system", "content": "You are a Level 1 IT Responder. Investigate server issues. "
                                      "If CPU or Memory is > 90%, restart the service. If logs show critical dependency errors (like connection refused) that a restart won't fix, escalate to an engineer. "
                                      "Format your FINAL response using Markdown with visual status emojis like 🟢 HEALTHY, ⚠️ RESTARTED, or 🚨 ESCALATED."},
        {"role": "user", "content": user_issue}
    ]

    try:
        while True:
            logging.info("Agent is evaluating conversation context payload...")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools_schema,
                tool_choice="auto"
            )

            response_msg = response.choices[0].message
            messages.append(response_msg)

            if response_msg.tool_calls:
                for tool_call in response_msg.tool_calls:
                    func_name = tool_call.function.name
                    try:
                        func_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError as ex:
                        error_fallback = f"Failed to parse function arguments via JSON payload: {str(ex)}"
                        logging.error(error_fallback)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": json.dumps({"error": error_fallback})
                        })
                        continue

                    function_to_call = AVAILABLE_FUNCTIONS.get(func_name)

                    if function_to_call:
                        try:
                            tool_output = function_to_call(**func_args)
