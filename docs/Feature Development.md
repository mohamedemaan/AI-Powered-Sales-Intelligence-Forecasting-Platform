# FEATURE DEVELOPMENT GUIDE

## 1. Purpose

This document defines the standard workflow for planning, implementing, testing, and maintaining features in the AI-Powered Sales Intelligence and Prediction Platform.

The goal is to deliver reliable features while preserving existing functionality, architecture, security, and user experience.

This guide describes the expected development process. It does not confirm that any feature is already implemented.

## 2. Core Principles

Every feature must follow these principles:

- Understand the requirement before coding.
- Inspect the existing implementation before making changes.
- Reuse existing components and services where appropriate.
- Preserve working functionality.
- Follow established coding and naming conventions.
- Keep changes focused and maintainable.
- Validate inputs and handle errors safely.
- Test relevant success and failure scenarios.
- Update documentation when behavior or configuration changes.
- Report actual verification results accurately.

## 3. Feature Development Lifecycle

Follow this lifecycle for each feature:

1. Requirement analysis.
2. Existing codebase inspection.
3. Feature planning.
4. Design and API planning.
5. Implementation.
6. Frontend and backend integration.
7. Testing and quality checks.
8. Security and performance review.
9. Documentation updates.
10. Completion report.

Not every feature requires a database or API change. Apply only the steps relevant to its scope.

## 4. Step 1 — Understand the Requirement

Before development, identify:

- The user problem.
- The intended user or role.
- Expected behavior.
- Required inputs.
- Expected outputs.
- Dependencies.
- Error conditions.
- Security considerations.
- Acceptance criteria.

Clarify ambiguous requirements before making assumptions that could affect the architecture or data.

## 5. Step 2 — Inspect Existing Code

Search the repository for related functionality.

Inspect relevant:

- Frontend pages and components.
- API routes and service modules.
- Database models.
- Data-processing functions.
- ML pipelines and model interfaces.
- Authentication and authorization logic.
- Tests.
- Configuration and environment variables.

Determine whether the feature already exists partially or completely.

Do not create duplicate routes, components, services, or database models without a clear reason.

## 6. Step 3 — Create a Feature Plan

Before implementation, define the smallest complete change.

Document:

- Feature objective.
- Files likely to change.
- Files that may need to be created.
- Frontend changes.
- Backend changes.
- Database changes, if required.
- API changes, if required.
- Security implications.
- Test scenarios.
- Acceptance criteria.
- Rollback or compatibility concerns.

Avoid unrelated refactoring during feature development.

## 7. Step 4 — Design the User Experience

For user-facing features, define:

- Page or component placement.
- Navigation behavior.
- Loading state.
- Empty state.
- Success state.
- Error state.
- Form validation.
- Responsive layout.
- Accessibility requirements.

Reuse the current design system, typography, colors, spacing, and component patterns.

Do not redesign unrelated screens unless the requirement explicitly calls for it.

## 8. Step 5 — Implement the Backend

When backend changes are needed:

1. Inspect existing route and service patterns.
2. Define request and response schemas.
3. Validate incoming data.
4. Implement the business logic.
5. Enforce authentication and authorization where required.
6. Handle database operations safely.
7. Return appropriate HTTP status codes.
8. Use consistent error responses.
9. Add suitable logging.
10. Create or update tests.

Keep business logic separate from route handlers when consistent with the existing architecture.

Do not invent endpoints or request fields without implementing and documenting them.

## 9. Step 6 — Implement the Frontend

When frontend changes are needed:

1. Identify the correct page or component.
2. Reuse existing UI components where possible.
3. Connect to the correct API service.
4. Validate user inputs.
5. Handle loading and failure states.
6. Display returned data accurately.
7. Check responsive behavior.
8. Verify accessibility.
9. Avoid unnecessary state and duplicated API requests.
10. Test the updated interaction.

Do not replace real backend data with hardcoded mock data unless explicitly requested.

If temporary mock data is necessary for development, clearly identify it and avoid presenting it as live application data.

## 10. Step 7 — Integrate Frontend and Backend

Verify the complete data flow:

1. User performs an action.
2. Frontend validates the input.
3. Frontend sends the correct request.
4. Backend validates and authorizes the request.
5. Business logic processes the data.
6. Database or ML services are used where required.
7. Backend returns the documented response.
8. Frontend displays the result.
9. Errors are handled clearly.

Check API URLs, request methods, headers, field names, data types, and response structures.

Do not assume that matching endpoint names guarantee a working integration.

## 11. Sales Data Import Features

For a feature involving sales data uploads or imports, verify the applicable requirements:

- Supported file formats.
- File size restrictions.
- Required columns.
- Data type validation.
- Date and currency handling.
- Missing values.
- Duplicate records.
- Malformed files.
- Unauthorized access.
- Storage behavior.
- Useful validation error messages.

Reject unsafe or invalid input rather than trusting uploaded content.

Do not expose one customer's data to another customer if the application supports multiple users or tenants.

## 12. Sales Analytics Features

For analytics changes, verify:

- Metric definitions.
- Date-range behavior.
- Filter behavior.
- Aggregation logic.
- Currency and unit consistency.
- Missing-data handling.
- Empty result behavior.
- Pagination or limits where applicable.
- Consistency between dashboard values and API responses.

Use the same business definitions across the frontend, backend, and documentation.

Do not fabricate metrics when source data is unavailable.

## 13. Forecasting Features

For sales forecasting changes, verify:

- Required historical data.
- Target variable.
- Forecast horizon.
- Time interval.
- Data preprocessing.
- Training and inference behavior.
- Model version.
- Evaluation method.
- Missing-data handling.
- Prediction output format.

Use chronological validation for time-series forecasting when appropriate.

Compare performance against a suitable baseline. Select evaluation metrics based on the business problem.

Forecasts are estimates, not guaranteed outcomes. Clearly communicate limitations and uncertainty where supported.

## 14. Anomaly Detection Features

For anomaly detection changes, verify:

- Input data quality.
- Detection method.
- Threshold configuration.
- Score or classification meaning.
- False-positive behavior.
- Missing-data handling.
- Explanation of detected anomalies where available.

Do not automatically label an unusual observation as fraud or a confirmed business failure.

## 15. Recommendation Features

For business recommendations, verify:

- Data supporting the recommendation.
- Business rules or model logic.
- Relevant time range.
- Expected user action.
- Explanation of the recommendation.
- Limitations and confidence, if supported.

Recommendations should be traceable to actual data or documented rules.

Do not claim that a recommendation will guarantee revenue growth or prevent losses.

## 16. Database Changes

If a feature requires database changes:

1. Inspect existing models and relationships.
2. Determine whether a schema change is necessary.
3. Follow the existing migration strategy.
4. Preserve existing records.
5. Add suitable constraints and indexes.
6. Validate data integrity.
7. Test migrations where possible.
8. Update database documentation.

Do not perform destructive operations on important databases without explicit authorization and a verified recovery plan.

## 17. Security Review

Before completing a feature, check:

- Input validation.
- Authentication requirements.
- Authorization requirements.
- Tenant or ownership checks, where applicable.
- Sensitive-data exposure.
- File upload security.
- Rate and resource limits, where needed.
- Secret management.
- Error-message safety.
- Logging of sensitive information.

Refer to `docs/SECURITY.md` and `AUTHENTICATION_SECURITY.md` for the relevant requirements.

## 18. Testing Strategy

Choose tests based on the feature's behavior and risk.

### Unit Tests

Verify individual functions, components, and business rules.

### Integration Tests

Verify interactions between components, APIs, databases, and external services.

### UI Tests

Verify user interactions, validation, loading states, and displayed results.

### Regression Tests

Verify that related existing features still work after the change.

### ML Validation

Where applicable, verify data preprocessing, inference outputs, model evaluation, and expected behavior on representative datasets.

Run the tests that actually exist in the repository. Add appropriate tests when necessary.

## 19. Performance Review

For features that may process large datasets or expensive calculations, evaluate:

- Response latency.
- Database query performance.
- Memory usage.
- Large file handling.
- Repeated API requests.
- Model inference time.
- Concurrent execution.
- Resource limits.

Measure before and after changes when claiming a performance improvement.

Avoid adding caching or background processing without considering data consistency, failure handling, and operational complexity.

## 20. Documentation Updates

Update relevant documentation when a feature changes:

- Product requirements.
- UI/UX behavior.
- System architecture.
- Database schema.
- API contracts.
- Environment variables.
- Security requirements.
- Setup instructions.
- Test instructions.
- Deployment procedures.
- Changelog.

Do not mark planned features as implemented merely because they appear in documentation.

## 21. Acceptance Criteria Template

Use this template for each new feature.

### Feature Name
[Enter feature name]

### User Problem
[Describe the problem]

### Expected Behavior
[Describe the intended behavior]

### Inputs
[List required inputs]

### Outputs
[List expected outputs]

### Error Scenarios
[List failure and invalid-input cases]

### Security Requirements
[List applicable security requirements]

### Testing Requirements
[List relevant tests]

### Acceptance Criteria
- [ ] Expected behavior works.
- [ ] Invalid inputs are handled safely.
- [ ] Relevant errors are handled.
- [ ] Frontend and backend integration is verified, if applicable.
- [ ] Database changes are validated, if applicable.
- [ ] Security requirements are addressed.
- [ ] Relevant tests have been executed.
- [ ] Documentation has been updated.
- [ ] Existing functionality has been checked for regressions.

## 22. Definition of Done

A feature is complete only when:

- Its requirements are satisfied.
- The implementation follows existing architecture.
- Relevant integrations work.
- Applicable security checks are addressed.
- Relevant tests have been executed.
- Known limitations are documented.
- Documentation reflects the actual behavior.
- The implementation has been reviewed.
- Verification results are reported honestly.

If some checks cannot be completed, report the feature as partially verified or blocked rather than fully verified.

## 23. AI Coding Agent Workflow

When an AI coding agent receives a feature request:

1. Read `AGENTS.md`.
2. Read the relevant product and technical documentation.
3. Inspect the current Git status.
4. Search for existing related functionality.
5. Present a concise implementation plan.
6. Make focused changes.
7. Preserve unrelated user changes.
8. Avoid unnecessary dependency or architecture changes.
9. Run relevant tests and validation.
10. Review the final diff.
11. List files changed.
12. Report test results, limitations, and remaining work.

Do not claim that commands were executed or tests passed unless this was actually verified.

## 24. Feature Completion Report

### Summary
[Describe the feature]

### Files Changed
[List changed files]

### Behavior Implemented
[Describe verified behavior]

### Tests Executed
[List actual test commands and results]

### Known Limitations
[List remaining issues]

### Final Status
[Completed and verified / Implemented but partially verified / In progress / Blocked]

## 25. Maintenance

Review this document whenever the development workflow, architecture, quality requirements, or feature implementation standards change.

Keep the guide consistent with the current codebase.