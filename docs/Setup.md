# SETUP GUIDE

## 1. Purpose

This document explains how to prepare the development environment, install dependencies, configure services, and run the Sales Prediction Dashboard locally.

The commands in this guide must be checked against the actual repository structure, dependency manifests, and startup scripts before execution.

## 2. Before You Start

Inspect the existing project and identify:

- Frontend framework and required runtime version.
- Backend framework and required runtime version.
- Package managers and dependency lockfiles.
- Database engine and connection requirements.
- Environment-variable configuration.
- Existing development and test commands.
- Required external services, if any.

Do not assume every optional technology listed in this document is installed or required.

## 3. Prerequisites

Install the tools required by the actual project.

| Tool | Purpose |
|---|---|
| Git | Source control |
| Node.js | Required if the frontend uses Node.js |
| npm, pnpm, or Yarn | Frontend dependency management |
| Python | Required if the backend uses Python |
| Python virtual environment | Isolates backend dependencies |
| Database engine | Stores application data, if required |
| Code editor | Development and debugging |

Use the versions declared by the repository. Do not upgrade runtimes or dependencies without checking compatibility.

## 4. Step 1 — Open the Project

Open the existing project directory in VS Code.

Verify the working directory and inspect the repository:

```bash
git status
```

Check the root directory and locate:

- Frontend directory.
- Backend directory.
- Dependency manifests.
- Lockfiles.
- Environment templates.
- Database configuration.
- Existing README and setup documentation.

If the repository contains uncommitted changes, preserve them.

## 5. Step 2 — Install Frontend Dependencies

Perform this step only if a separate frontend exists.

Navigate to the actual frontend directory:

```bash
cd frontend
```

Inspect `package.json` and the available lockfile.

For an npm project with `package-lock.json`, use:

```bash
npm ci
```

If the project does not have a compatible `package-lock.json`, follow its existing package-manager instructions instead.

Do not mix npm, pnpm, and Yarn in the same project without an intentional migration.

### Verify Frontend Setup

Review the available scripts in `package.json`.

Start the development server using the existing script. For example, if the project defines a `dev` script:

```bash
npm run dev
```

Check the terminal for compilation errors and use the local URL printed by the application.

The port may differ depending on the configuration or whether the default port is occupied.

## 6. Step 3 — Set Up the Backend

Perform this step only if a separate backend exists.

Navigate to the actual backend directory:

```bash
cd backend
```

### Python Environment

If the backend uses Python, create an isolated environment where appropriate.

On Windows:

```powershell
py -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, follow your organization's security policy or use an alternative supported terminal. Do not weaken system-wide security settings merely to activate a virtual environment.

For Command Prompt:

```bat
.venv\Scripts\activate.bat
```

For Linux or macOS:

```bash
source .venv/bin/activate
```

### Install Backend Dependencies

Use the dependency manager declared by the project.

For a project that uses `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

For a project managed through `pyproject.toml`, follow its documented installation workflow.

Do not install both dependency sets blindly if the project has a different package-management strategy.

### Start the Backend

Inspect the backend entry point and available scripts.

For example, if the application is a FastAPI service whose import path is `app.main:app`, the development command may be:

```bash
uvicorn app.main:app --reload
```

This is an example only. Replace it with the correct command for the actual application structure.

Use development reload settings only in local development.

## 7. Step 4 — Configure Environment Variables

Find the existing environment template and configuration documentation.

Typical steps:

1. Identify required environment variables from the codebase.
2. Create a local environment file in the location expected by the application.
3. Set the correct local API URL.
4. Configure the database connection, if required.
5. Add authentication secrets only where needed.
6. Configure external service credentials only when required.
7. Restart affected services after changing configuration.

Never commit real credentials or production secrets.

Do not invent environment-variable names. Use the names that the application actually reads.

Refer to `ENVIRONMENT.md` for detailed configuration guidance.

## 8. Step 5 — Configure the Database

If the project requires a database:

1. Identify the database engine and version.
2. Start the database service.
3. Create or select a development database.
4. Configure the connection string.
5. Apply existing migrations using the project's documented process.
6. Load seed data only if a supported seed process exists.
7. Verify connectivity.

Do not assume the project uses PostgreSQL, MySQL, or SQLite until confirmed.

Do not run destructive reset commands against a database containing important data.

## 9. Step 6 — Start Required Services

Start each service in the order required by the application.

A common development arrangement may include:

- Database service.
- Backend API.
- Frontend development server.
- Optional workers or ML services.

Use separate terminals when services must run concurrently.

Do not assume every service is required or that each service uses a particular port.

## 10. Step 7 — Verify the Application

Check the following items where applicable.

### Frontend

- [ ] Development server starts.
- [ ] Main page loads.
- [ ] No critical browser-console errors occur.
- [ ] Static assets load correctly.
- [ ] API requests use the intended backend URL.

### Backend

- [ ] Server starts successfully.
- [ ] Imports and dependencies load.
- [ ] Required environment variables are present.
- [ ] API routes respond as expected.
- [ ] Errors are logged appropriately.

### Database

- [ ] Database service is reachable.
- [ ] Connection settings are correct.
- [ ] Required migrations have been applied.
- [ ] Basic read/write operations work where appropriate.

### Sales and ML Features

If implemented:

- [ ] Sample sales data can be validated.
- [ ] Analytics endpoints return the expected structure.
- [ ] Forecasting workflows execute successfully.
- [ ] Model artifacts load correctly.
- [ ] Charts display the returned data correctly.
- [ ] Empty or invalid datasets are handled safely.

Only mark a check as complete after actually verifying it.

## 11. Step 8 — Run Tests

Review `TESTING.md` and the scripts defined in the repository.

Run the appropriate checks, which may include:

- Unit tests.
- API tests.
- Frontend tests.
- Type checking.
- Linting.
- Build verification.
- Database integration tests.
- ML evaluation tests.

Use the project's real commands. Record failures instead of ignoring them.

## 12. Troubleshooting

### Dependency Installation Fails

Check:

- Runtime version compatibility.
- Package-manager version.
- Lockfile consistency.
- Network connectivity.
- The complete error message.

Avoid deleting lockfiles or reinstalling all dependencies as the first response.

### Frontend Does Not Start

Check:

- The current working directory.
- The available scripts in `package.json`.
- Environment-variable configuration.
- Port conflicts.
- Dependency installation.
- Compilation errors.

### Backend Does Not Start

Check:

- Python version.
- Virtual environment activation.
- Dependency installation.
- Application import path.
- Missing configuration.
- Port conflicts.
- Traceback details.

### Frontend Cannot Reach Backend

Check:

- Backend server status.
- API base URL.
- CORS configuration.
- Network errors.
- Protocol and port settings.
- Authentication requirements.

Do not disable security protections globally to make a request succeed.

### Database Connection Fails

Check:

- Database status.
- Host and port.
- Database name.
- Credentials.
- Network permissions.
- Connection-string format.
- Migration status.

Never include real passwords in shared logs or screenshots.

### Forecasting or ML Fails

Check:

- Dataset format.
- Required columns.
- Input validation.
- Model artifact path.
- Dependency versions.
- Available memory.
- Model-loading errors.

Do not claim a forecasting result is correct merely because an API returned a response.

## 13. Safe Development Practices

- Keep local secrets out of version control.
- Use development data rather than confidential customer data.
- Preserve existing source files and configuration.
- Review changes before committing.
- Avoid destructive database commands.
- Do not disable authentication or authorization to bypass errors.
- Keep production configuration separate from development configuration.
- Document manual setup steps that are necessary to reproduce the environment.

## 14. AI Coding Agent Instructions

When asked to set up or repair the development environment, the AI coding agent must:

1. Inspect the repository before running commands.
2. Identify the actual package manager and startup scripts.
3. Check the current Git working tree.
4. Preserve existing user changes.
5. Avoid unnecessary dependency upgrades.
6. Never print or commit secrets.
7. Run only relevant, understood commands.
8. Verify startup and connectivity where possible.
9. Report the commands actually executed.
10. Clearly explain any step that remains unverified.

Do not report a successful setup unless the relevant checks have passed.

## 15. Setup Completion Checklist

- [ ] Repository structure inspected.
- [ ] Required runtimes identified.
- [ ] Dependencies installed.
- [ ] Environment variables configured.
- [ ] Database configured, if required.
- [ ] Backend starts, if present.
- [ ] Frontend starts, if present.
- [ ] Required services are reachable.
- [ ] Basic application workflows verified.
- [ ] Relevant tests executed.
- [ ] Known setup limitations documented.

## 16. Maintenance

Update this guide whenever dependency management, runtime requirements, environment configuration, startup commands, or database setup changes.

Keep all instructions consistent with the actual repository.