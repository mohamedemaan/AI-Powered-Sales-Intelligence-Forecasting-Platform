# PROJECT IMPLEMENTATION GUIDE

## 1. Purpose

This document defines the implementation workflow for the AI-Powered Sales Intelligence and Prediction Platform.

It guides developers and AI coding agents through repository inspection, feature implementation, integration, testing, and verification while preserving existing project functionality.

This document describes the development process. It does not confirm that every planned feature is already implemented.

## 2. Implementation Principles

Every implementation must follow these principles:

- Inspect the existing codebase before making changes.
- Preserve working features and established application behavior.
- Follow the current architecture and coding conventions.
- Reuse existing utilities, services, and components where appropriate.
- Avoid unnecessary rewrites and dependency changes.
- Make small, focused, testable changes.
- Validate all user inputs and external data.
- Handle errors without exposing sensitive information.
- Update tests and documentation when behavior changes.
- Verify results before reporting a task as complete.

## 3. Initial Repository Assessment

Before implementing a feature, inspect the repository.

### 3.1 Frontend Assessment

Identify:

- Framework and version.
- Application entry points.
- Page and route structure.
- Reusable UI components.
- API client configuration.
- Data-fetching logic.
- State management.
- Charting and visualization libraries.
- Styling conventions.
- Existing authentication flows, if implemented.

### 3.2 Backend Assessment

Identify:

- Backend framework and entry point.
- API routes and request schemas.
- Business logic and service modules.
- Database models and repositories.
- Authentication and authorization middleware.
- Input validation.
- Error-handling patterns.
- Logging and monitoring.
- Existing test coverage.

### 3.3 Data and ML Assessment

Identify:

- Supported input formats.
- Dataset validation and preprocessing.
- Feature engineering logic.
- Existing forecasting models.
- Model training and inference workflows.
- Evaluation metrics.
- Model artifact storage.
- Anomaly detection logic.
- Recommendation generation.
- Data leakage and validation safeguards.

### 3.4 Configuration Assessment

Review:

- Dependency manifests and lockfiles.
- Environment variables.
- Database configuration.
- Docker configuration, if present.
- CI/CD workflows, if present.
- Deployment settings.
- Existing documentation and instructions.

Record findings before proposing major structural changes.

## 4. Feature Implementation Workflow

Every feature should follow this workflow.

### Step 1: Understand the Requirement

- Read the relevant product requirement.
- Identify the user problem being solved.
- Define expected inputs and outputs.
- Identify dependencies and constraints.
- Clarify acceptance criteria.

### Step 2: Inspect Existing Functionality

- Search for related routes, components, services, and models.
- Check whether part or all of the feature already exists.
- Identify reusable code.
- Identify regressions or integration risks.
- Avoid duplicating existing functionality.

### Step 3: Prepare the Implementation Plan

Define:

- Files expected to change.
- New files required, if any.
- API and database changes.
- Frontend and backend responsibilities.
- Security considerations.
- Test cases.
- Rollback considerations for risky changes.

Keep the plan proportional to the feature.

### Step 4: Implement the Smallest Complete Change

- Follow existing conventions.
- Keep responsibilities separated.
- Reuse existing abstractions where appropriate.
- Avoid unrelated refactoring.
- Avoid hardcoded secrets and environment-specific URLs.
- Preserve compatibility where required.

### Step 5: Integrate Components

Verify that:

- Frontend requests match backend API contracts.
- Request and response schemas agree.
- Database models match required data.
- Errors are handled consistently.
- Authentication and authorization are enforced where required.
- Loading, empty, success, and failure states are handled in the UI.

### Step 6: Test the Change

Run relevant tests and validation checks.

Where applicable, verify:

- Expected behavior.
- Invalid input handling.
- Missing data handling.
- Error scenarios.
- Permission checks.
- API integration.
- Database operations.
- Existing functionality that could be affected.

### Step 7: Review and Document

- Review the code diff.
- Check for accidental changes.
- Remove temporary debugging output.
- Update documentation and tests.
- Record known limitations.
- Report exactly what was verified.

## 5. Core Application Workflows

The following workflows describe intended behavior. Confirm their implementation status in the existing codebase.

### 5.1 Sales Data Ingestion

Expected workflow:

1. User supplies a supported sales dataset.
2. The application validates the file and input format.
3. The backend validates required columns and data types.
4. Invalid rows or records are reported appropriately.
5. Valid data is normalized and processed.
6. The application stores or processes the data according to the existing architecture.
7. The user receives a clear success or failure result.

Important considerations:

- File size limits.
- Supported file formats.
- Missing values.
- Duplicate records.
- Invalid dates and numeric values.
- Unexpected columns.
- Malformed files.
- Unauthorized data access.

### 5.2 Sales Analytics

Expected workflow:

1. Retrieve authorized sales data.
2. Apply the required filters and time ranges.
3. Calculate the relevant business metrics.
4. Return structured results.
5. Display metrics and charts.
6. Handle empty datasets and API failures.

Metric definitions must be consistent across the frontend, backend, and documentation.

### 5.3 Sales Forecasting

Expected workflow:

1. Validate the selected dataset and forecasting inputs.
2. Prepare the required historical time series.
3. Apply the configured preprocessing steps.
4. Load or train the selected model according to the existing design.
5. Generate forecasts.
6. Evaluate results where appropriate.
7. Return predictions and relevant metadata.
8. Display results with suitable explanations and limitations.

Forecasting requirements should define:

- Forecast horizon.
- Time interval.
- Required historical data.
- Target sales metric.
- Model version.
- Evaluation method.
- Missing-data behavior.
- Prediction uncertainty, when supported.

Do not present unverified predictions as guaranteed future outcomes.

### 5.4 Anomaly Detection

Expected workflow:

1. Validate the relevant sales or operational data.
2. Apply the configured detection method.
3. Identify unusual observations.
4. Return anomaly scores or classifications where supported.
5. Explain relevant contributing signals where available.
6. Display findings with appropriate context.

An anomaly indicates unusual behavior; it does not automatically prove fraud, data corruption, or a business failure.

### 5.5 Business Recommendations

Expected workflow:

1. Retrieve authorized analytics and forecast results.
2. Evaluate the configured business rules or recommendation logic.
3. Generate relevant recommendations.
4. Include supporting evidence where available.
5. Return recommendations with clear limitations.
6. Display results in the dashboard.

Recommendations must not claim evidence that the system has not actually calculated.

## 6. Frontend Implementation Requirements

When modifying frontend functionality:

- Follow the existing component structure.
- Reuse established design patterns.
- Maintain responsive layouts.
- Use consistent spacing, typography, and colors.
- Include loading and error states.
- Handle empty datasets gracefully.
- Keep API calls separate from presentation where appropriate.
- Validate forms before submission.
- Avoid exposing private configuration in browser code.
- Ensure interactive elements are accessible.
- Avoid unnecessary re-renders and expensive computations.

For charts, verify that axes, units, labels, tooltips, and date ranges are correct.

Do not replace an existing design system without an explicit requirement.

## 7. Backend Implementation Requirements

When modifying backend functionality:

- Keep route handlers focused.
- Separate business logic where appropriate.
- Validate incoming requests.
- Enforce authorization for protected resources.
- Use appropriate HTTP status codes.
- Return consistent response structures.
- Handle database transactions safely.
- Avoid leaking internal exceptions to clients.
- Add suitable logging.
- Apply timeouts and limits where necessary.
- Avoid blocking operations in asynchronous request handlers without an appropriate strategy.

Use the existing framework and architectural patterns unless a documented decision supports changing them.

## 8. Database Implementation Requirements

Before changing database structures:

1. Inspect existing models and relationships.
2. Review current schema and migration history.
3. Identify compatibility risks.
4. Plan the required migration.
5. Preserve existing records.
6. Validate constraints and indexes.
7. Test migration and rollback procedures where supported.
8. Update relevant documentation.

Do not delete production data or run destructive migrations without explicit authorization and a verified recovery plan.

## 9. Machine Learning Implementation Requirements

For ML-related changes:

- Establish a reproducible preprocessing pipeline.
- Prevent target leakage.
- Split time-series data chronologically where appropriate.
- Compare models against a suitable baseline.
- Select evaluation metrics appropriate to the forecasting task.
- Document model assumptions.
- Record relevant model versions and parameters.
- Handle missing and unexpected input data.
- Test inference with representative inputs.
- Monitor prediction quality when monitoring is implemented.

Possible forecasting metrics include MAE, RMSE, and MAPE. MAPE requires special care when actual values are zero or near zero.

Model performance must be measured rather than assumed.

## 10. API Integration Requirements

Before changing an endpoint:

- Review the API documentation.
- Confirm request and response schemas.
- Validate field names and types.
- Check authentication requirements.
- Check pagination and filtering behavior, if applicable.
- Confirm error responses.
- Update frontend consumers when contracts change.
- Add or update API tests.

Avoid silently breaking existing API consumers.

## 11. Security Requirements

All implementations must follow the project's security requirements.

At minimum:

- Validate and sanitize untrusted inputs.
- Enforce authorization on protected operations.
- Keep secrets out of source control.
- Protect uploaded files.
- Restrict cross-origin access appropriately.
- Avoid logging sensitive customer data.
- Apply appropriate resource limits.
- Use secure authentication and session practices.
- Avoid exposing stack traces or internal configuration to users.

Refer to `docs/SECURITY.md` for detailed security guidance.

## 12. Testing and Verification

Testing should be proportional to the risk and scope of the change.

Potential checks include:

- Unit tests.
- API tests.
- Frontend component tests.
- Database integration tests.
- Data validation tests.
- Forecasting evaluation.
- End-to-end tests.
- Build and type checks.
- Manual regression checks.

Run only commands supported by the actual project configuration.

If a check cannot be run, state the reason. Do not claim that it passed.

Refer to `docs/TESTING.md`.

## 13. Performance and Reliability

When relevant, evaluate:

- Large dataset processing.
- Database query efficiency.
- API response latency.
- Expensive model inference.
- Memory consumption.
- Concurrent requests.
- File upload limits.
- Caching correctness.
- Background job handling.

Do not introduce caching, parallel processing, or background workers without understanding consistency, failure handling, and operational requirements.

Measure performance before claiming an optimization is successful.

## 14. Implementation Completion Criteria

A feature may be reported as complete only when its applicable criteria are satisfied:

- [ ] Requirements and acceptance criteria are understood.
- [ ] Existing implementation was inspected.
- [ ] Code follows repository conventions.
- [ ] Frontend and backend contracts are consistent.
- [ ] Database changes are safe and documented.
- [ ] Security requirements are addressed.
- [ ] Relevant tests have been executed.
- [ ] Build or validation checks have been completed where applicable.
- [ ] Existing functionality has been checked for regressions.
- [ ] Documentation has been updated.
- [ ] Known limitations are recorded.
- [ ] Actual verification results are reported accurately.

Not every feature requires every type of test. Document justified exceptions.

## 15. AI Coding Agent Rules

When implementing tasks, an AI coding agent must:

1. Read `AGENTS.md` and relevant documentation.
2. Inspect the current repository state.
3. Identify the actual implementation and dependencies.
4. Explain the proposed change before broad refactoring.
5. Modify only the files necessary for the task.
6. Preserve unrelated user changes.
7. Avoid inventing API endpoints, database fields, or environment variables.
8. Avoid replacing real functionality with mock data unless requested.
9. Run relevant checks after changes.
10. Review the final diff.
11. Report changed files and executed tests.
12. Clearly identify unverified behavior and remaining work.

Never claim a task is complete merely because code was generated.

## 16. Implementation Report Template

Use the following structure when reporting completed work:

### Summary
Describe the requested change.

### Files Changed
List the modified and created files.

### Implementation Details
Explain the main technical decisions.

### Validation
List the commands and tests actually executed.

### Results
Report successful checks and any failures.

### Remaining Issues
Document unresolved problems, limitations, and follow-up work.

### Status
Use an accurate status such as:

- Completed and verified.
- Implemented but partially verified.
- In progress.
- Blocked.
- Not implemented.

## 17. Maintenance

Update this document when the implementation workflow, core architecture, validation requirements, or project conventions change.

Keep implementation guidance aligned with the actual repository and the approved product requirements.