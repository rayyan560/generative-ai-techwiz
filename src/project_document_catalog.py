PROJECT_DOCUMENTS = {
    "srs": {
        "title": "Project Documentation / SRS",
        "subtitle": "Project scope, requirements and Generative AI capabilities",
        "icon": "fa-file-contract",
        "topics": ["Project Introduction", "Problem Statement", "Proposed Solution", "Objectives", "Scope", "Functional Requirements", "Non-Functional Requirements", "User Roles", "AI Features", "Limitations", "Future Enhancements"],
        "files": [("Open SRS PDF", "/project-docs/file/srs.pdf", "fa-file-pdf")],
    },
    "user-guide": {
        "title": "User Manual / User Guide",
        "subtitle": "A practical walkthrough of the SupportNova portal",
        "icon": "fa-book-open-reader",
        "topics": ["Website Access", "Registration and Login", "AI Interface", "Prompt Submission", "File and Data Upload", "AI-Generated Output", "Chat and History", "Download and Export", "Error Handling", "Major Feature Walkthrough"],
        "files": [("Read User Guide", "/project-docs/file/user-guide.html", "fa-arrow-up-right-from-square")],
    },
    "developer-guide": {
        "title": "Developer Guide / Technical Documentation",
        "subtitle": "Architecture, integrations, configuration and operations",
        "icon": "fa-code",
        "topics": ["Project Architecture", "Python Environment", "FastAPI Structure", "Frontend Structure", "AI/API Integration", "MongoDB Integration", "CSV/JSON Processing", "Prompt Handling", "AI Response Processing", "Dependencies", "Configuration", "Error Handling and Logging"],
        "files": [("Read Developer Guide", "/project-docs/file/developer-guide.html", "fa-arrow-up-right-from-square")],
    },
    "architecture": {
        "title": "Architecture, DFD & UML",
        "subtitle": "Visual system design and end-to-end data movement",
        "icon": "fa-diagram-project",
        "topics": ["System Architecture Diagram", "Context Diagram", "Level 0 DFD", "Level 1 DFD", "AI Request Flow", "Authentication Flow", "Use Case Diagram", "Class Diagram", "Sequence Diagram", "Activity Diagram", "Component Diagram", "Deployment Diagram"],
        "files": [
            ("Open Project Documentation", "/project-docs/file/slides.html", "fa-images"),
            ("Read Comprehensive Report (DFD/UML)", "/project-docs/file/project-report.md", "fa-file-lines"),
        ],
    },
    "database": {
        "title": "Database Documentation",
        "subtitle": "MongoDB collections, fields, relationships and backups",
        "icon": "fa-database",
        "topics": ["MongoDB Database Design", "Collections", "Documents and Fields", "Relationships and References", "Sample Documents", "Database Schema", "MongoDB Backup", "Database Initialization Script", "Users", "Conversations", "Prompts", "AI Responses", "Uploaded Files", "Feedback and Logs"],
        "files": [("Open Project Documentation", "/project-docs/file/slides.html", "fa-images")],
    },
    "setup": {
        "title": "Installation, Configuration & Test Data",
        "subtitle": "Everything needed to run, configure and verify the project",
        "icon": "fa-screwdriver-wrench",
        "topics": ["Python Installation", "Virtual Environment", "Required Python Version", "Libraries", "MongoDB Setup", "Gemini API Configuration", ".env Configuration", "Running the Application", "Browser Access", "Troubleshooting", "Test Data", "Sample Prompts", "Expected Outputs"],
        "files": [("Open Project Documentation", "/project-docs/file/slides.html", "fa-images")],
    },
    "slides": {
        "title": "Project Presentation Slides",
        "subtitle": "A ready-to-present slide deck covering all project topics",
        "icon": "fa-chalkboard-user",
        "topics": ["Project Overview", "Problem and Solution", "Features", "User Journey", "Technical Architecture", "Data Flow", "AI Pipeline", "Database Design", "Security", "Installation", "Testing", "Limitations", "Future Roadmap"],
        "files": [("Open 50-Slide Deck", "/project-docs/file/slides.html", "fa-play")],
    },
    "demo-videos": {
        "title": "Project Demo Videos",
        "subtitle": "Voice-over browser walkthroughs of the project and its documentation",
        "icon": "fa-circle-play",
        "topics": ["Full Project Walkthrough", "Authentication and Documents Walkthrough"],
        "files": [
            ("Play Full Project Walkthrough", "/project-docs/file/project-walkthrough.mp4", "fa-play"),
            ("Play Authentication & Documents Walkthrough", "/project-docs/file/auth-docs-walkthrough.mp4", "fa-play"),
        ],
    },
}

PROJECT_FILES = {
    "srs.pdf": "SupportNova-Generative AI PowerPlay_SRS.pdf",
    "user-guide.html": "SupportNova_User_Guide.html",
    "developer-guide.html": "SupportNova_Developer_Guide.html",
    "slides.html": "SupportNova_50_Slides_Project_Documentation.html",
    "project-report.md": "PROJECT_REPORT.md",
    "project-walkthrough.mp4": "video_assets/SupportNova_Project_Walkthrough_VoiceOver.mp4",
    "auth-docs-walkthrough.mp4": "video_assets/SupportNova_Authentication_Documents_VoiceOver.mp4",
}
