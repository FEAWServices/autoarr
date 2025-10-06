Perfect! Now I understand the AutoArr project. This is an intelligent orchestration layer for the *arr media automation stack. Let me define a comprehensive set of Claude agents tailored specifically for this project with TDD, SAST, DAST, and documentation requirements.

## AutoArr Claude Agent Architecture

### **1. Orchestrator Agent (Master Conductor)**
**Primary Role**: Coordinates all agents and manages the development workflow

**Responsibilities**:
- Parses user stories and technical requirements
- Delegates tasks to specialized agents based on component (MCP servers, LLM integration, UI, etc.)
- Enforces quality gates (tests pass, security scans clear, docs updated)
- Manages the TDD cycle across all agents
- Coordinates releases and versioning
- Tracks dependencies between tasks
- Generates sprint reports and progress updates

**Key Prompts**:
```
You are the Orchestrator for the AutoArr project. Analyze this requirement: [requirement]. 
Break it into tasks, assign to appropriate agents, and define the acceptance criteria.
Ensure TDD approach is followed.
```

---

### **2. MCP Server Development Agent**
**Primary Role**: Builds and maintains MCP servers for SABnzbd, Sonarr, Radarr, and Plex

**Responsibilities**:
- Writes TDD tests for MCP server endpoints
- Implements MCP protocol compliance
- Creates API wrapper functions
- Handles authentication and rate limiting
- Implements error handling and retry logic
- Ensures idempotent operations
- Documents MCP server capabilities

**Technology Focus**: 
- Python/TypeScript for MCP servers
- API integration patterns
- WebSocket connections
- JSON-RPC

**Test Requirements**:
- Unit tests for each MCP tool/resource
- Integration tests with mock APIs
- Contract tests for API compatibility

---

### **3. LLM Integration Agent**
**Primary Role**: Develops the intelligent decision-making layer

**Responsibilities**:
- Designs prompt engineering for configuration recommendations
- Implements LLM context management
- Builds natural language parsing for user requests
- Creates classification logic (movie vs. TV show)
- Develops web search integration for best practices
- Implements caching and performance optimization
- Fine-tuning coordination (when applicable)

**Technology Focus**:
- Claude API integration
- Prompt engineering
- RAG (Retrieval Augmented Generation)
- Vector databases for documentation

**Test Requirements**:
- Unit tests for prompt templates
- Integration tests for LLM responses
- Performance tests for inference latency
- Cost tracking tests

---

### **4. Event Processing Agent**
**Primary Role**: Builds the event-driven architecture

**Responsibilities**:
- Designs event schemas
- Implements webhook handlers
- Creates polling mechanisms for applications without webhooks
- Builds event queue management
- Implements retry and dead letter queues
- Creates event correlation logic
- Writes event processors (failed downloads, wanted items, etc.)

**Technology Focus**:
- Event-driven patterns
- Message queues (Redis, RabbitMQ)
- Async processing
- State machines

**Test Requirements**:
- Event handler unit tests
- Integration tests for event flows
- Load tests for event processing
- Chaos engineering for failure scenarios

---

### **5. Frontend Development Agent**
**Primary Role**: Builds the mobile-first web UI

**Responsibilities**:
- Writes TDD tests for React components
- Implements responsive design
- Creates dashboard visualizations
- Builds chat interface for NL requests
- Implements configuration audit UI
- Develops PWA capabilities
- Ensures accessibility (WCAG 2.1)

**Technology Focus**:
- React/Vue.js/Svelte
- Tailwind CSS
- WebSocket for real-time updates
- PWA APIs

**Test Requirements**:
- Component unit tests (Jest/Vitest)
- Integration tests (React Testing Library)
- E2E tests (Playwright/Cypress)
- Visual regression tests
- Accessibility tests

---

### **6. Backend API Agent**
**Primary Role**: Develops the REST API and business logic

**Responsibilities**:
- Writes TDD tests for API endpoints
- Implements authentication/authorization
- Creates configuration audit logic
- Builds recommendation engine
- Implements download recovery logic
- Develops health monitoring
- Creates audit logging

**Technology Focus**:
- FastAPI/Express.js/Go
- JWT/OAuth
- PostgreSQL/MongoDB
- Redis caching

**Test Requirements**:
- API unit tests
- Integration tests
- Contract tests (OpenAPI)
- Load/stress tests

---

### **7. Docker/Infrastructure Agent**
**Primary Role**: Manages containerization and deployment

**Responsibilities**:
- Creates Dockerfiles with TDD approach
- Writes docker-compose configurations
- Implements health checks
- Creates volume management
- Builds secrets management
- Develops backup/restore procedures
- Creates deployment scripts

**Technology Focus**:
- Docker
- Docker Compose
- Kubernetes (future)
- CI/CD pipelines

**Test Requirements**:
- Container smoke tests
- Integration tests for multi-container setup
- Security scanning of images
- Performance tests

---

### **8. SAST Security Agent**
**Primary Role**: Performs static code security analysis

**Responsibilities**:
- Scans Python/JS/TS code for vulnerabilities
- Reviews MCP server security
- Checks for hardcoded secrets/credentials
- Validates input sanitization
- Reviews authentication implementations
- Scans dependencies for CVEs
- Ensures OWASP Top 10 compliance

**Tools Integration**:
- Bandit (Python)
- ESLint with security plugins
- Semgrep
- Snyk/Dependabot
- SonarQube

**Scanning Scope**:
- All MCP servers
- Backend API code
- Frontend code
- Docker configurations
- CI/CD pipelines

**Reports**:
- Vulnerability severity (Critical/High/Medium/Low)
- Remediation recommendations
- Compliance reports

---

### **9. DAST Security Agent**
**Primary Role**: Performs dynamic security testing on running application

**Responsibilities**:
- Tests authentication/authorization bypasses
- Checks for injection vulnerabilities (SQL, NoSQL, Command)
- Validates session management
- Tests API security (rate limiting, input validation)
- Checks for SSRF vulnerabilities
- Tests webhook security
- Validates CORS policies
- Tests for sensitive data exposure

**Tools Integration**:
- OWASP ZAP
- Burp Suite
- Custom security test suite

**Testing Scenarios**:
- MCP server API endpoints
- REST API endpoints
- WebSocket connections
- File upload/download
- External API integrations

---

### **10. Test Architect Agent (TDD Specialist)**
**Primary Role**: Ensures comprehensive test coverage and TDD compliance

**Responsibilities**:
- Designs test strategies for each component
- Writes test specifications before implementation
- Creates test data factories
- Implements mutation testing
- Ensures 80%+ code coverage
- Creates integration test scenarios
- Designs E2E test flows
- Maintains test documentation

**Test Pyramid Focus**:
- Unit tests: 70%
- Integration tests: 20%
- E2E tests: 10%

**Special Focus Areas**:
- MCP protocol compliance testing
- API contract testing
- Event processing testing
- LLM response validation
- Configuration validation

---

### **11. Documentation Agent**
**Primary Role**: Creates and maintains all project documentation

**Responsibilities**:
- Writes API documentation (OpenAPI/Swagger)
- Creates MCP server documentation
- Generates architecture diagrams (C4 model)
- Writes user guides and tutorials
- Maintains README and CONTRIBUTING files
- Creates video tutorial scripts
- Writes deployment guides
- Documents configuration options
- Creates troubleshooting guides
- Maintains changelog

**Documentation Types**:
1. **Technical Docs**:
   - Architecture Decision Records (ADRs)
   - API reference
   - MCP server specifications
   - Database schemas
   - Event schemas

2. **User Docs**:
   - Installation guide
   - Quick start guide
   - Configuration guide
   - Troubleshooting
   - FAQ

3. **Developer Docs**:
   - Contributing guide
   - Development setup
   - Testing guide
   - Release process
   - Code style guide

---

### **12. Integration Testing Agent**
**Primary Role**: Tests inter-component communication

**Responsibilities**:
- Tests MCP server ↔ Backend integration
- Tests Backend ↔ Frontend integration
- Tests External API integrations (SABnzbd, Sonarr, etc.)
- Tests LLM integration flows
- Tests event flow across components
- Creates integration test environments
- Validates data consistency

**Test Scenarios**:
- User requests content → Classification → Radarr/Sonarr
- Failed download → Event → Recovery logic → New search
- Configuration audit → LLM recommendation → Apply change
- Web search → Context gathering → LLM analysis

---

### **13. Performance & Load Testing Agent**
**Primary Role**: Ensures system performance and scalability

**Responsibilities**:
- Creates load test scenarios
- Tests concurrent user handling
- Validates LLM inference performance
- Tests event processing throughput
- Identifies bottlenecks
- Creates performance budgets
- Tests database query performance
- Validates caching effectiveness

**Tools**:
- k6/Gatling
- Apache JMeter
- Custom scripts

**Key Metrics**:
- API response time (p95, p99)
- LLM inference latency
- Event processing rate
- Database query time
- Frontend rendering time

---

### **14. Code Review Agent**
**Primary Role**: Performs comprehensive code reviews

**Responsibilities**:
- Reviews code quality and style
- Checks adherence to Python/JS/TS best practices
- Validates SOLID principles
- Reviews error handling
- Checks logging practices
- Validates test quality
- Reviews security implementations
- Ensures code documentation
- Checks for code smells

**Review Checklist**:
- Code follows project style guide
- Tests are comprehensive and meaningful
- Error handling is robust
- Logging is appropriate
- Security best practices followed
- Performance considerations addressed
- Documentation is complete

---

### **15. Compliance & Privacy Agent**
**Primary Role**: Ensures legal and privacy compliance

**Responsibilities**:
- Reviews API ToS compliance
- Ensures no user data leaves container (privacy-first)
- Validates GDPR considerations
- Reviews open source license compatibility
- Ensures neutral language (no piracy associations)
- Reviews premium feature boundaries
- Validates logging practices (no PII)

**Focus Areas**:
- SABnzbd API ToS
- Sonarr API ToS
- Radarr API ToS
- Plex API ToS
- Claude API terms
- MIT license compatibility

---

## Workflow Example: Adding Natural Language Content Request Feature

```
1. Orchestrator receives requirement: "Implement NL content request"

2. Orchestrator breaks down:
   - Frontend chat interface
   - Backend API endpoint
   - LLM classification logic
   - MCP server integration
   - Event handling
   
3. Test Architect Agent creates test specifications:
   - Unit tests for chat component
   - API endpoint tests
   - LLM classification tests
   - Integration test for full flow
   
4. Parallel execution:
   - Frontend Agent: Builds chat UI (TDD)
   - Backend API Agent: Creates endpoint (TDD)
   - LLM Integration Agent: Implements classification (TDD)
   - MCP Server Agent: Ensures ready
   
5. Integration Testing Agent validates complete flow

6. SAST Agent scans all new code:
   - Input validation
   - No injection vulnerabilities
   - Authentication checks
   
7. DAST Agent tests running feature:
   - API security
   - Rate limiting
   - Input fuzzing
   
8. Performance Agent validates:
   - Response time < 2s
   - Concurrent request handling
   - LLM inference latency
   
9. Documentation Agent updates:
   - API docs
   - User guide
   - Architecture diagram
   
10. Code Review Agent reviews all PRs

11. Compliance Agent verifies:
    - No user data logged
    - API usage within ToS
    
12. Orchestrator validates all gates passed → Merge to main
```

---

## CI/CD Pipeline Integration

**Pre-commit**:
- Code linting
- Unit tests
- SAST scan

**Pull Request**:
- All tests (unit + integration)
- Code coverage check (80% minimum)
- SAST full scan
- Code review (agent + human)

**Main Branch**:
- Full test suite
- SAST + DAST scans
- Performance tests
- Documentation build
- Docker image build
- Security scan of image

**Release**:
- Full regression suite
- Load tests
- DAST full scan
- Documentation deployment
- Docker image push
- Release notes generation

---

## Agent Interaction Matrix

| Agent | Talks To | Provides | Receives |
|-------|----------|----------|----------|
| Orchestrator | All | Tasks, priorities | Status, blockers |
| Test Architect | All dev agents | Test specs | Implementation updates |
| SAST Agent | Code Review, Orchestrator | Vulnerability reports | Code changes |
| DAST Agent | Integration Testing, Orchestrator | Security test results | Running environments |
| Documentation | All agents | Docs | Implementation details |

---

## Technology-Specific Recommendations

**Python** (MCP Servers, Backend):
- pytest for testing
- Bandit for SAST
- FastAPI for APIs
- Pydantic for validation

**TypeScript/JavaScript** (Frontend, possibly MCP):
- Vitest/Jest for testing
- ESLint + security plugins for SAST
- React Testing Library
- Playwright for E2E

**Docker**:
- Multi-stage builds
- Non-root user
- Security scanning with Trivy

**Documentation**:
- MkDocs or Docusaurus
- OpenAPI for API docs
- Mermaid for diagrams

---

Would you like me to create detailed prompt templates for any specific agent, or shall I help you set up the initial project structure with these agents in mind?