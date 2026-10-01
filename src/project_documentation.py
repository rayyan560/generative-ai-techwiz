ADDITIONAL_TOPIC_DETAILS = {
    "Limitations": (
        "SupportNova provides decision support, not an automatic warranty or refund decision. Results depend on the submitted details, the policy corpus, the database and the configured Gemini service.",
        ["Short or ambiguous reports can reduce classification quality", "Gemini or MongoDB outages can delay automated analysis", "Staff must review eligibility, safety and high-impact outcomes"],
    ),
    "Website Access": (
        "Open the deployed SupportNova public URL in a current browser. The customer complaint form is on the landing page; staff tools and project documents require an authorized portal session.",
        ["Use the public customer portal to create or track a case", "Use the Admin Portal or Agent Portal for role-appropriate operations", "The documents library is under Project Documents & Slides in the admin navigation"],
    ),
    "Registration and Login": (
        "Customers can use the account and registration controls on the portal. Staff authenticate through the login page; available dashboards are determined by the account role and deployment configuration.",
        ["Enter the account email and password on the login page", "Use only credentials issued for the competition demonstration", "A protected session is required for staff tools and document downloads"],
    ),
    "AI Interface": (
        "The customer portal combines structured complaint fields with an optional assistant, a deterministic intake preview and staff-reviewed case tracking. AI output is presented as assistance rather than a final decision.",
        ["Describe the issue in the complaint title and details fields", "Use the optional assistant for general support guidance", "Use the rule-based preview as an estimate, not an approval"],
    ),
    "Prompt Submission": (
        "The complaint form is the primary structured request interface. The backend validates the title and description, normalizes the request and builds contextual prompts from the case and applicable knowledge before calling Gemini when configured.",
        ["Provide a descriptive title of at least three characters", "Describe the incident in at least ten characters", "Do not include passwords, payment card data or unrelated personal information"],
    ),
    "File and Data Upload": (
        "Photo evidence is optional. A supported image is checked for type and size; if a customer consents and Gemini vision is configured, the image is analyzed for review notes and the original is not retained.",
        ["Supported image types are JPEG, PNG, WebP and GIF", "The upload limit is 10 MB", "Photo interpretation is advisory and must be reviewed by staff"],
    ),
    "AI-Generated Output": (
        "The analysis pipeline can produce issue category, urgency, priority, sentiment, extracted entities, policy context and suggested next steps. Deterministic Python validation is compared with Gemini output; conflicts can require manual review.",
        ["Read the status and analysis fields as recommendations", "Check cited policy and comparison warnings before acting", "If automated analysis is unavailable, the case remains available for staff review"],
    ),
    "Chat and History": (
        "The portal provides live customer-support messaging and a case history view. Conversation messages are associated with an anonymous or authenticated client session; complaint history is scoped to the signed-in customer.",
        ["Open Live Chat & Call Requests to start a support conversation", "Open My Complaints to review cases belonging to the current account", "Use the ticket reference and matching email in the public tracking flow"],
    ),
    "Download and Export": (
        "Authorized reviewers can open the project SRS PDF, user guide, developer guide, slide deck and walkthrough videos from the project-document pages. Spreadsheet exports depend on the dashboard and the selected view.",
        ["Open Project Documents & Slides from the admin navigation", "Use the source-document links to open or download the selected item", "Treat exported case data as confidential and share it only with authorized reviewers"],
    ),
    "Error Handling": (
        "The form reports missing or too-short required fields before a valid request is accepted. API errors are returned with an explanatory message; transient service failures leave the customer able to retry after checking the entered details.",
        ["Use a complaint title with at least three characters", "Use an incident description with at least ten characters", "If an error persists, retain its request details and contact the project operator"],
    ),
    "Major Feature Walkthrough": (
        "The project walkthrough videos demonstrate the main customer, staff and documentation routes. They are browser-playable demonstrations, not a collection of annotated still screenshots.",
        ["The full walkthrough covers the main project portal and workflows", "The authentication-and-documents walkthrough shows where the project materials are located", "Screens can differ slightly by account role, theme or deployment state"],
    ),
    "CSV/JSON Processing": (
        "The application uses JSON fixtures for complaint demonstration data and local fallback storage, while pandas supports tabular analysis and exports. Hosted deployments use the configured MongoDB database rather than an ephemeral local store.",
        ["The complaint seed fixture is sample_complaints/complaints_500.json", "CSV/JSON parsing and analytics should validate input before processing", "Never replace the live database with a local fixture during deployment"],
    ),
    "Context Diagram": (
        "At context level, SupportNova sits between customers, support staff, administrators, Gemini and MongoDB. Customers provide complaint details; staff review case recommendations and update outcomes.",
        ["Customers submit, track and discuss complaints", "Agents and administrators review and manage cases", "Gemini and MongoDB are external services configured by the deployment"],
    ),
    "Level 0 DFD": (
        "The level-0 data-flow view groups the system into intake, identity and access, complaint analysis, knowledge retrieval, case operations and reporting processes.",
        ["Complaint intake validates customer and product details", "Analysis combines policy context, Python rules and optional Gemini output", "Operations dashboards read case and audit data for staff review"],
    ),
    "Level 1 DFD": (
        "The level-1 view expands case analysis into normalization, entity extraction, policy retrieval, deterministic validation, optional model inference, comparison and persistence.",
        ["A complaint is created with a stable case reference before background analysis", "Analysis results and review status are written back to the case record", "Audit events record important automated or staff actions"],
    ),
    "Use Case Diagram": (
        "The main actors are customer, agent, administrator and judge. Their use cases are separated by role; judge access is read-only while staff access follows the granted role.",
        ["Customers submit, track and message about their own cases", "Agents triage, communicate and update assigned operational cases", "Administrators manage dashboards, knowledge, rules and access"],
    ),
    "Class Diagram": (
        "The model layer represents complaints, analysis outputs, deterministic ground truth, comparison results, extracted entities and audit events as distinct data shapes.",
        ["ComplaintSubmission carries the customer report and case metadata", "GenAIIntelligenceOutput and PythonGroundTruthResult represent separate analyses", "ComparisonResult records agreement, warnings and review requirements"],
    ),
    "Sequence Diagram": (
        "A submission sequence starts in the browser, passes through the FastAPI complaint endpoint and input checks, creates a case record, then runs analysis in a background task and reports status to staff views.",
        ["The API validates title, description and optional image consent", "The initial case is stored synchronously for immediate tracking", "Background analysis updates the case and emits a staff notification when available"],
    ),
    "Activity Diagram": (
        "The complaint activity begins with form entry and validation, branches on photo consent and data validity, then creates a case and routes it through automated analysis or a manual-review fallback.",
        ["Invalid input returns field guidance without creating a case", "Valid input receives a complaint reference", "Unavailable or conflicting analysis routes the case to human review"],
    ),
    "Component Diagram": (
        "The main components are FastAPI routes, Jinja templates and browser scripts, domain services, the policy knowledge manager, Gemini integration and database adapters.",
        ["routers/ separates authentication, warranty, chat, admin and analytics endpoints", "src/ contains reusable validation, retrieval and analysis modules", "config/database.py provides MongoDB access and the guarded local development fallback"],
    ),
    "Deployment Diagram": (
        "The hosted deployment runs the web service on Railway and connects it to MongoDB Atlas and optional Google Gemini APIs through environment configuration. The local workflow uses a developer machine and virtual environment.",
        ["Railway serves the FastAPI application and static assets", "MongoDB Atlas is the persistent hosted data store", "Secrets and service endpoints belong in deployment variables, never in source control"],
    ),
    "MongoDB Database Design": (
        "The data layer uses MongoDB collections for operational cases, users, knowledge documents, document chunks, rules, escalation rules, audit events and live chat. Some analysis is embedded in the complaint record.",
        ["Collection accessors are centralized in config/database.py", "Related records share identifiers such as complaint_id and document_id", "Hosted persistence requires an available, correctly configured MongoDB connection"],
    ),
    "Documents and Fields": (
        "Records are stored as BSON-compatible dictionaries. Complaint documents hold the customer report, product, status, timestamps, analysis results and review fields; knowledge metadata and chunks use document identifiers.",
        ["ComplaintSubmission and analysis Pydantic models define important field shapes", "Audit records include actor, action, time and event details", "Optional values may be absent when a customer did not provide them"],
    ),
    "Relationships and References": (
        "The application links related records through stable business identifiers rather than requiring a relational join. A complaint can be referenced by audit and chat data; knowledge chunks refer to their source document.",
        ["complaint_id connects case analysis and audit activity", "document_id connects knowledge metadata and parsed chunks", "user_id and normalized email support customer ownership checks"],
    ),
    "Sample Documents": (
        "Sample policy documents are read from the repository's configured docs directory and parsed into knowledge metadata and chunks during initialization. The complaint demo fixture is maintained separately as JSON.",
        ["Policy PDFs and DOCX documents are parsed by the document-processing module", "A sample policy's version and status are recorded for retrieval", "Sample data must be clearly distinguished from real customer records"],
    ),
    "Database Schema": (
        "MongoDB records are flexible documents rather than a single SQL schema. Pydantic models describe key complaint and analysis payloads; collection-specific field names are visible in the database access and router modules.",
        ["Core collections include complaints, users and live_chats", "Knowledge uses knowledge_documents and document_chunks", "Rules and review trails use rule_matrix, escalation_rules and audit_logs"],
    ),
    "MongoDB Backup": (
        "Backup and restore are deployment-operator responsibilities. The application code does not claim to perform managed Atlas snapshots or guarantee point-in-time recovery.",
        ["Configure and verify backups in the MongoDB provider for the deployment", "Test a restore into an isolated environment before relying on it", "Never place database credentials or backup archives in the public repository"],
    ),
    "Database Initialization Script": (
        "Application startup launches non-blocking initialization that loads the policy knowledge base and seeds the complaint fixture when the complaints collection is empty.",
        ["KnowledgeBaseManager parses configured policy documents into metadata and chunks", "The complaint fixture is sample_complaints/complaints_500.json", "Hosted startup requires persistent MongoDB; seed only an empty demo collection"],
    ),
    "Users": (
        "User records support authentication, role checks and account ownership. Passwords are handled by the authentication module; operational UI access must be protected by the assigned role.",
        ["Roles include customer, agent, administrator and read-only judge", "Customer case history is scoped to the authenticated identity", "Do not publish real user records or passwords in documentation"],
    ),
    "Conversations": (
        "Live chat messages are stored in the live_chats collection and grouped by a client identifier. Case-linked staff communication can also be associated with a complaint reference.",
        ["Chat endpoints create and retrieve conversation messages", "Authenticated customer history is scoped to the current user", "Conversation text can contain personal data and must be access-controlled"],
    ),
    "Prompts": (
        "Prompts are composed at request time from the complaint, relevant policy and task instructions. The application does not expose a separate prompt-history collection in its database access layer.",
        ["Prompt templates are maintained in src/prompt_templates", "User-provided text is treated as untrusted input", "Only context needed for the current analysis should be sent to an external model"],
    ),
    "AI Responses": (
        "Gemini analysis is represented by structured output and stored with the corresponding complaint record when analysis succeeds. The deterministic result and comparison record remain separately identifiable within the case.",
        ["Model output can include category, urgency, sentiment and next steps", "Comparison fields expose disagreement and manual-review requirements", "A provider failure records a safe analysis status instead of an invented result"],
    ),
    "Uploaded Files": (
        "Complaint photos are checked for supported image format and size, read for the optional analysis flow and not retained as original image files. The case records whether evidence was attached.",
        ["Photo upload is optional and limited to 10 MB", "Explicit consent is required before an image is sent for model analysis", "The application does not maintain a standalone uploaded-file collection"],
    ),
    "Feedback and Logs": (
        "Important automated and staff actions can be recorded in audit_logs. A separate customer feedback collection is not currently configured; do not present audit entries as a complete feedback-management system.",
        ["Audit entries identify the case, actor, action, time and details", "Application logs support operational diagnosis and should not reveal secrets", "Feedback collection and retention policy remain a future enhancement"],
    ),
    "Python Installation": (
        "Install a supported CPython release from the official Python distribution source, then confirm the interpreter is available before creating the project environment.",
        ["Use a currently supported Python 3 release compatible with requirements.txt", "On Windows, enable the Python launcher or add Python to PATH", "The repository does not currently pin an exact interpreter patch version"],
    ),
    "Virtual Environment": (
        "Use an isolated virtual environment so the project dependencies do not modify the global Python installation. The repository's local .venv is development state and is not part of the deployment.",
        ["Create an environment with python -m venv .venv", "Activate it before installing packages", "Install dependencies from requirements.txt and exclude the environment from Git"],
    ),
    "Required Python Version": (
        "The application requires a modern Python 3 runtime compatible with FastAPI, Pydantic v2 and the listed dependencies. The repository does not pin a precise minor or patch release, so align local and hosted runtimes and run the tests after upgrades.",
        ["Use a supported CPython 3 release", "The codebase and dependencies are validated in the project's test environment", "Pin a runtime version explicitly before a production runtime upgrade"],
    ),
    "Libraries": (
        "Runtime libraries are declared in requirements.txt. FastAPI and Uvicorn serve the app; Pydantic validates data; PyMongo connects to MongoDB; Google GenAI provides optional Gemini calls; Jinja2 renders pages.",
        ["Install with pip install -r requirements.txt", "Document parsers, pandas and NumPy support knowledge and analysis workflows", "Keep dependency changes reviewed and run the automated test suite afterward"],
    ),
    "MongoDB Setup": (
        "Hosted operation expects MONGODB_URI to reference the isolated SupportNova database and requires successful connectivity. The service intentionally refuses to start with an ephemeral local store on Railway.",
        ["Create a database and restricted application user in MongoDB Atlas", "Set MONGODB_URI and DATABASE_NAME in the host's secret variables", "Confirm network access and deployment health without exposing the URI"],
    ),
    "Gemini API Configuration": (
        "Optional model analysis uses the Google Gemini client and reads its key from GEMINI_API_KEYS or GOOGLE_GENAI_API_KEY. The selected model name is controlled by GEMINI_MODEL; deterministic validation remains available as a fallback.",
        ["Set provider keys only in a private local environment or Railway variable store", "Choose a model supported by the configured Google GenAI account", "Never include API values in screenshots, commits or demonstration output"],
    ),
    ".env Configuration": (
        "Local secrets and service settings are read from environment variables, with a local .env file supported by config/settings.py. Hosted values belong in Railway's variable manager; the .env file is ignored by Git.",
        ["Configure database, session, model and base-URL settings privately", "Use .env.example as a safe reference if present", "Do not paste or commit real tokens, database URLs or passwords"],
    ),
    "Browser Access": (
        "Once the web process is healthy, open its public BASE_URL or the configured local host in a current browser. The portal is responsive and uses browser support for optional voice dictation and media playback.",
        ["Check the /health endpoint if the page does not load", "Use HTTPS for the hosted deployment and secure session cookies", "Allow optional browser features only when the user chooses them"],
    ),
    "Sample Prompts": (
        "A useful test prompt describes a specific product issue and includes relevant order, date or symptom details without sharing secrets. Example: 'My NovaBook screen flickers after the latest update; order ORD-12345, purchased on 2026-09-12.'",
        ["Include symptoms and relevant dates to support entity extraction", "Avoid sensitive payment details and authentication secrets", "Treat any suggested policy outcome as requiring staff review"],
    ),
    "Expected Outputs": (
        "For a valid complaint, the system returns a complaint reference and initial processing status. Later analysis may add category, urgency, priority, policy context and a review recommendation; provider failure routes the case to manual review.",
        ["A valid title has at least three characters and details at least ten", "The initial success response includes a CMP- case identifier", "No specific model conclusion or resolution time is guaranteed"],
    ),
    "Problem and Solution": (
        "The presentation frames inconsistent, slow manual complaint handling as the problem and SupportNova's structured, policy-aware workflow as the proposed solution.",
        ["Capture consistent customer and product details", "Combine deterministic policy checks with optional GenAI assistance", "Keep staff accountable for decisions and resolution"],
    ),
    "User Journey": (
        "The demonstration journey moves from opening the portal through complaint entry, validation, case reference creation, automated or manual review, staff handling and customer tracking.",
        ["Customer submits details and optional consented evidence", "The system assigns a case reference and analysis status", "Staff review the case while customers use the tracking workflow"],
    ),
    "AI Pipeline": (
        "The analysis pipeline normalizes a complaint, retrieves relevant policy context, executes deterministic Python validation, requests optional Gemini analysis and compares results before surfacing recommendations.",
        ["Input checks and policy context run before model analysis", "Ground-truth rules and model output are compared", "Conflicts, missing context or service outages can require human review"],
    ),
    "Security": (
        "Security controls include signed sessions, role-aware routes, judge read-only restrictions, request validation, consent for image analysis and environment-based secrets. These controls reduce risk but do not replace a formal security audit.",
        ["Use least-privilege accounts and unique session secrets", "Keep database and model credentials out of source control", "Validate authorization, privacy and provider handling before a production launch"],
    ),
    "Installation": (
        "The local demo is installed into an isolated Python environment, configured with the required data services, then started with the repository's FastAPI application command.",
        ["Install dependencies from requirements.txt", "Provide a reachable MongoDB database and private environment settings", "Start the server and verify /health before opening the portal"],
    ),
    "Limitations": (
        "The demonstration does not establish production-scale performance, guaranteed AI accuracy, managed backups or continuous availability. Model analysis depends on provider access and policy-data quality.",
        ["Human review remains mandatory for warranty, refund and safety outcomes", "Provider errors may leave a case pending manual review", "Load, security and recovery targets require separate operational validation"],
    ),
    "Full Project Walkthrough": (
        "This voice-over browser walkthrough introduces the SupportNova portal and demonstrates its main customer and operations workflows from start to finish.",
        ["Use the Full Project Walkthrough link to play the MP4 in the browser", "The video is a demonstration and does not create or modify a case", "For current behavior, use the live portal and its role permissions"],
    ),
    "Authentication and Documents Walkthrough": (
        "This voice-over browser walkthrough shows the authentication landing page and where the project documents and slide materials can be found in the portal.",
        ["Use the Authentication & Documents Walkthrough link to play the MP4", "Project materials are under Admin Portal → Project Documents & Slides", "The login role determines which protected pages are available"],
    ),
}
