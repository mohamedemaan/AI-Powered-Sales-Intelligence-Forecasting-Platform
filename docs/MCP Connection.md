# MCP Connection Guide

## 1. Purpose

This document explains how to evaluate, configure, connect, test, and troubleshoot Model Context Protocol (MCP) integrations for the Sales Prediction Dashboard / AI-Powered Sales Intelligence Platform.

MCP can provide a standardized way for compatible AI applications to access approved tools, resources, and prompts.

**Important:** MCP integration status must be verified against the existing codebase. This document describes the recommended implementation approach; it does not confirm that MCP has already been implemented.

---

## 2. What Is MCP?

Model Context Protocol (MCP) is a protocol that allows compatible AI applications to communicate with external tools and data sources through a standardized interface.

### Core Components

| Component | Responsibility |
|---|---|
| MCP Host | The AI application that manages the interaction |
| MCP Client | Establishes and manages a connection to an MCP server |
| MCP Server | Exposes approved tools, resources, or prompts |
| Tools | Actions that an AI application can request |
| Resources | Data that a client can read when supported |
| Prompts | Reusable prompt templates exposed by a server |

### Example Project Workflow

1. A user uploads sales data.
2. The backend validates and processes the data.
3. The forecasting service generates predictions.
4. An authorized AI assistant requests an approved tool, if MCP integration is configured.
5. The tool returns structured results.
6. The assistant explains the results to the user.

MCP does not automatically create forecasting models or business logic. Those capabilities must exist in the application or be implemented separately.

---

## 3. Recommended Integration Architecture

```text
User
 |
 v
Frontend Dashboard
 |
 v
Backend API
 |
 +----------------------+
 |                      |
 v                      v
Sales Forecasting    AI Assistant
Service                  |
                          v
                     MCP Client
                          |
                          v
                      MCP Server
                          |
                          v
                Approved Application Tools
                          |
                          v
             Validated Sales Data / Analytics
```

### Architecture Rules

- Keep business logic inside the appropriate backend services.
- Use MCP only when a compatible host or AI application needs standardized access to approved capabilities.
- Keep authentication and authorization in place.
- Validate tool inputs and outputs.
- Do not expose unrestricted database access through MCP.
- Do not expose private customer data unless explicitly authorized and necessary.
- Avoid creating a second implementation of an existing business operation.

---

## 4. Before Implementing MCP

Inspect the existing project before making changes.

Check:

- Backend framework and current API structure.
- Existing AI assistant or LLM integration.
- Current authentication and authorization system.
- Database access layer.
- Sales forecasting and analytics services.
- Existing MCP dependencies, configuration, and server entry points.
- Deployment environment and supported transport options.

### Suggested Inspection Commands

Run commands from the project root.

```bash
# Check Git changes
git status

# Search for existing MCP references
git grep -n -i "mcp"

# Search for environment configuration files
git ls-files "*env*" "*.toml" "*.yaml" "*.yml" "*.json"
```

These commands are intended for source inspection. Review their output before changing any files.

If MCP is already configured, document and improve the existing integration instead of creating a duplicate server.

---

## 5. Choose the Correct MCP Connection Type

The transport depends on the MCP client, server, deployment environment, and SDK version.

### Option A: Local Process / Standard I/O

Use a local process-based connection when a compatible host launches an MCP server as a subprocess and communicates through standard input and output.

Considerations:

- The server process must be executable in the host environment.
- The host must support the selected MCP client configuration.
- Standard output must not contain unrelated logs that interfere with protocol messages.
- Required dependencies and environment variables must be available to the process.

### Option B: Streamable HTTP

Use Streamable HTTP when the MCP server is deployed as a network service and the client supports that transport.

Considerations:

- Use HTTPS in production.
- Configure authentication according to the host and server capabilities.
- Validate incoming requests.
- Apply request timeouts and resource limits.
- Configure network access and origin protections where applicable.

### Important

Do not assume that every MCP client supports every transport or configuration format. Verify the documentation for the specific client and SDK version before configuring a connection.

Avoid copying legacy transport examples into a new implementation without checking current compatibility.

---

## 6. MCP Server Responsibilities

An MCP server for this platform should expose only well-defined, authorized operations.

Possible tools include:

| Tool | Purpose | Access considerations |
|---|---|---|
| `get_sales_summary` | Return an aggregate sales summary | Enforce tenant scope |
| `get_forecast` | Retrieve an existing forecast | Validate forecast and tenant identifiers |
| `analyze_sales_trend` | Analyze approved historical sales data | Limit the requested time range |
| `get_inventory_alerts` | Retrieve inventory anomalies | Restrict access to authorized inventory |
| `get_business_recommendations` | Retrieve recommendations generated by the application | Avoid unsupported financial claims |

These are proposed tool names, not confirmed existing project functions.

Before registering a tool, verify that the underlying service exists. If it does not, implement and test the business operation separately.

### Tool Design Rules

Each tool should have:

- A clear name and description.
- A defined input schema.
- Input validation.
- Authentication and authorization checks.
- Tenant-aware data access where applicable.
- Predictable output.
- Safe error handling.
- Logging that avoids credentials and unnecessary personal data.
- Timeouts and appropriate resource limits.

Prefer read-only tools initially. Add write operations only when there is a clear business requirement and a secure authorization workflow.

---

## 7. Tool Input and Output Design

Tool schemas must match the selected MCP SDK and protocol version.

A conceptual example of a read-only tool is shown below. Treat this as a design illustration, not a drop-in implementation.

```json
{
  "name": "get_sales_summary",
  "description": "Return an authorized aggregate sales summary for a permitted date range.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "start_date": {
        "type": "string",
        "description": "Start date in YYYY-MM-DD format"
      },
      "end_date": {
        "type": "string",
        "description": "End date in YYYY-MM-DD format"
      }
    },
    "required": ["start_date", "end_date"],
    "additionalProperties": false
  }
}
```

### Validation Requirements

The implementation should:

1. Parse and validate both dates.
2. Reject invalid date ranges.
3. Apply reasonable limits to the requested range.
4. Determine the authenticated user's permissions.
5. Apply tenant and ownership restrictions.
6. Call the existing analytics service.
7. Return a structured result.
8. Handle failures without exposing internal stack traces.

Never trust a tenant ID, user ID, or permission claim supplied only as a tool argument. Derive access scope from trusted authentication context.

---

## 8. MCP Client Configuration

Configure the MCP client using the instructions for the actual AI host or application.

Configuration fields vary between clients. A conceptual local-process configuration might contain:

```json
{
  "mcpServers": {
    "sales-intelligence": {
      "command": "<verified-server-command>",
      "args": ["<verified-server-entry-point>"],
      "env": {
        "APP_ENV": "development"
      }
    }
  }
}
```

**This is a placeholder example.** Do not paste it into a real configuration without confirming the required format, command, entry point, and supported fields for the selected host.

For a remote server, use the exact connection format supported by the chosen client, including its documented authentication mechanism.

### Configuration Rules

- Never put real API keys, passwords, or access tokens in committed configuration files.
- Use environment variables or an approved secrets manager.
- Use separate credentials for development and production.
- Grant only the minimum required permissions.
- Do not assume that environment variables are automatically passed to a subprocess.
- Restart or reload the host when required by its configuration system.
- Keep configuration compatible with the deployed runtime.

---

## 9. Environment Variables and Secrets

Document required variables in the project's environment documentation.

For example, a future integration might require:

```dotenv
# Illustrative placeholders only
MCP_ENABLED=false
MCP_SERVER_URL=
MCP_AUTH_TOKEN=
```

These names are examples, not confirmed project variables.

### Secret Handling Rules

- Do not commit `.env` files containing real secrets.
- Provide safe placeholders in `.env.example`.
- Validate required settings during startup.
- Do not print tokens in logs or exception messages.
- Rotate exposed credentials immediately.
- Restrict secret access to the relevant service.
- Never send secrets to the model as ordinary prompt content.
- Keep production credentials outside source control.

If MCP is optional, the application should have a documented and tested behavior when the integration is disabled or unavailable.

---

## 10. Authentication and Authorization

MCP connectivity does not replace application-level access control.

Implement security checks at the server and underlying service boundaries.

Required considerations:

- Authenticate the connecting client using a supported mechanism.
- Authorize each tool invocation.
- Verify tenant ownership before returning data.
- Enforce role-based permissions where applicable.
- Prevent users from accessing other organizations' data.
- Validate resource identifiers.
- Apply rate limits and execution timeouts.
- Return generic client-facing errors for internal failures.

For remote deployments, use the authentication and security requirements documented by the chosen MCP implementation. Do not invent custom token forwarding or OAuth flows without understanding the client's supported authorization model.

### Prompt Injection Considerations

Treat sales records, uploaded CSV files, logs, and external tool output as untrusted data.

- Do not treat instructions embedded in data as trusted system instructions.
- Do not let tool output independently authorize another action.
- Require explicit authorization for sensitive operations.
- Restrict tool capabilities to the minimum necessary.
- Require confirmation for consequential write operations when appropriate.

---

## 11. Error Handling

The MCP server and its underlying services should handle common failures safely.

| Scenario | Expected behavior |
|---|---|
| Server unavailable | Return a controlled error and record the failure |
| Invalid input | Reject the request with a clear validation message |
| Unauthorized user | Deny access |
| Tenant mismatch | Deny access without leaking other tenant information |
| Forecast not found | Return a safe not-found result |
| Upstream service timeout | Apply a timeout and return a controlled error |
| Invalid tool output | Validate the result and report a safe failure |
| Rate limit exceeded | Reject or defer the request according to policy |

Do not silently substitute fabricated sales figures or forecasts when a tool fails.

If a fallback is implemented, clearly distinguish fallback results from live or model-generated results.

---

## 12. Testing the MCP Connection

Test the connection in a non-production environment before enabling it for real users.

### Connection Checklist

- [ ] Confirm the selected MCP host and SDK.
- [ ] Verify the configured transport.
- [ ] Confirm the server starts successfully.
- [ ] Confirm the client connects successfully.
- [ ] Confirm the server exposes only intended tools.
- [ ] Validate tool input schemas.
- [ ] Test successful tool execution.
- [ ] Test malformed inputs.
- [ ] Test missing and invalid credentials.
- [ ] Test tenant isolation.
- [ ] Test timeouts and server restarts.
- [ ] Verify logs do not contain secrets.
- [ ] Verify the application works safely when MCP is disabled.

### End-to-End Test

1. Sign in as an authorized test user.
2. Request an approved sales summary.
3. Confirm the correct tool is selected.
4. Confirm the server validates the request.
5. Confirm only authorized data is returned.
6. Confirm the assistant explains the actual result accurately.
7. Repeat with an unauthorized user and verify access is denied.

Do not use production customer data for initial integration testing.

---

## 13. Observability

If MCP is implemented, monitor:

- Connection success and failure counts.
- Tool invocation counts.
- Tool execution duration.
- Timeout and error rates.
- Rate-limit events.
- Authorization failures.
- Server process health.
- Dependency and upstream service health.

Use request or correlation IDs when supported.

Logs should contain enough information to diagnose failures without storing secrets, raw authentication headers, or unnecessary customer data.

Do not log complete prompts or tool payloads by default if they may contain confidential sales data.

---

## 14. Deployment Checklist

Before deploying an MCP integration:

- [ ] Verify the implementation against the selected SDK documentation.
- [ ] Confirm the deployment platform supports the required transport.
- [ ] Configure production secrets securely.
- [ ] Use HTTPS for remote connections.
- [ ] Configure authentication and authorization.
- [ ] Restrict network access where possible.
- [ ] Configure timeouts and resource limits.
- [ ] Verify tenant isolation.
- [ ] Configure monitoring and safe logging.
- [ ] Test restart and failure recovery.
- [ ] Document how to disable the integration.
- [ ] Confirm no development credentials are used in production.

If the MCP server is deployed separately from the main backend, document its deployment, access policy, environment variables, health checks, and release process.

---

## 15. Troubleshooting

### Problem: MCP Server Does Not Start

Check:

1. The configured command and entry point.
2. The installed runtime and dependencies.
3. Required environment variables.
4. File permissions and working directory.
5. Startup logs for configuration errors.

### Problem: Client Cannot Connect

Check:

1. Whether the server process or remote endpoint is running.
2. Whether the transport is supported by the client.
3. Whether the URL or process configuration is correct.
4. Whether network rules or proxies are blocking the connection.
5. Whether the server and client versions are compatible.

### Problem: Tools Are Not Listed

Check:

1. Whether tool registration completed successfully.
2. Whether the client refreshed its available tools.
3. Whether server initialization completed.
4. Whether the host supports the tool capability being used.
5. Whether schema or protocol errors appear in logs.

### Problem: Tool Returns Incorrect Sales Data

Check:

1. Date-range interpretation and timezone handling.
2. Tenant and user scoping.
3. Data preprocessing and aggregation logic.
4. Whether the tool calls the existing source of truth.
5. Whether cached results are stale.
6. Whether the returned output matches the underlying service response.

### Problem: Authorization Fails

Check:

1. Credential validity and expiration.
2. The documented authentication flow.
3. User roles and granted permissions.
4. Tenant ownership checks.
5. Server and client clock differences where relevant to token validation.

Do not resolve authentication failures by disabling authorization checks.

---

## 16. Instructions for AI Coding Agents

When implementing MCP in this repository:

1. Inspect the current codebase before editing.
2. Identify existing MCP-related code, dependencies, and configuration.
3. Confirm the actual backend framework and AI integration.
4. Check the official documentation for the selected MCP SDK and version.
5. Reuse existing analytics and forecasting services.
6. Do not invent APIs, environment variables, or installed dependencies.
7. Propose the smallest implementation that meets the requirement.
8. Preserve existing routes and application behavior.
9. Add input validation and authorization before exposing tools.
10. Add tests for successful calls, invalid input, and unauthorized access.
11. Run relevant tests and report their actual results.
12. Document every new dependency and configuration variable.
13. Never claim that a connection works unless it has been tested.
14. If MCP is unnecessary for the current architecture, explain why before introducing it.

---

## 17. Definition of Done

An MCP integration can be considered ready for review when:

- The selected client and server are documented.
- The transport is supported and configured correctly.
- Approved tools are registered and discoverable.
- Tool input validation is tested.
- Authentication and authorization are enforced.
- Tenant isolation is tested where applicable.
- Failures are handled safely.
- Secrets are not committed or logged.
- Monitoring and deployment requirements are documented.
- Tests pass in the target environment.
- The implementation status is based on verified evidence.

---

## 18. Final Note

This document is an implementation and operational guide, not proof that MCP is currently connected to the Sales Prediction Dashboard.

Before marking MCP as implemented, verify the server, client, tools, configuration, security controls, and end-to-end test results in the actual repository.

