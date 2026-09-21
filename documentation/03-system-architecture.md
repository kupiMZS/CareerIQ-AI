# System Architecture Document

# CareerIQ AI

---

# Document Information

| Field | Description |
|---|---|
| Project Name | CareerIQ AI |
| Document Type | System Architecture Document |
| Version | 1.0 |
| Architecture Style | Layered Modular Architecture |
| Backend Architecture | Laravel Modular Backend |
| AI Architecture | Independent AI Service |
| Database | MySQL 8.x |
| Cloud Platform | AWS |

---

# Table of Contents

1. Architecture Vision  
2. System Context Architecture  
3. High-Level Architecture  
4. Frontend Architecture  
5. Backend Architecture  
6. AI Intelligence Architecture  
7. Database Architecture  
8. Infrastructure Architecture  
9. Cloud Deployment Architecture  
10. Security Architecture  
11. CI/CD Architecture  
12. Scalability Strategy  
13. Technology Decisions  


---

# 1. Architecture Vision


## 1.1 Purpose


This document defines the technical architecture of CareerIQ AI.


The purpose is to describe:


- System components
- Application structure
- Data flow
- Communication between services
- Cloud deployment strategy
- Security model
- Scalability approach


CareerIQ AI is designed as a modern AI-powered career intelligence platform combining:


- Angular frontend
- Laravel backend
- MySQL database
- Python AI services
- AWS cloud infrastructure


---

# 2. System Context Architecture


## 2.1 Overview


The system connects users, application services, AI capabilities, and cloud infrastructure.


```mermaid
%%{init:{
'theme':'base',
'themeVariables':{
'fontFamily':'Inter',
'lineColor':'#94A3B8'
}
}}%%


flowchart TB


USER("Users<br/><br/>Students<br/>Graduates<br/>Professionals")


SYSTEM("CareerIQ AI Platform")


AIAPI("External AI Services<br/><br/>LLM APIs<br/>AI Models")


CLOUD("Cloud Infrastructure<br/><br/>AWS Services")



USER --> SYSTEM

SYSTEM --> AIAPI

SYSTEM --> CLOUD



classDef user fill:#334155,stroke:#CBD5E1,color:#FFFFFF;

classDef system fill:#7C3AED,stroke:#C4B5FD,color:#FFFFFF;

classDef ai fill:#D97706,stroke:#FCD34D,color:#FFFFFF;

classDef cloud fill:#0891B2,stroke:#67E8F9,color:#FFFFFF;


class USER user;

class SYSTEM system;

class AIAPI ai;

class CLOUD cloud;

```

---

# 3. High-Level Architecture


## 3.1 Architectural Layers


CareerIQ AI follows a layered architecture:


```
Presentation Layer

        ↓

Application Layer

        ↓

AI Intelligence Layer

        ↓

Data Layer

        ↓

Cloud Infrastructure Layer

```


---

## 3.2 Complete System Architecture


```mermaid
%%{init:{
'theme':'base',
'themeVariables':{
'fontFamily':'Inter',
'lineColor':'#94A3B8'
}
}}%%


flowchart TB


USER("Users")


subgraph PRESENTATION["Presentation Layer"]

ANGULAR("Angular Frontend<br/><br/>TypeScript<br/>Tailwind CSS")

end


subgraph APPLICATION["Application Layer"]

LARAVEL("Laravel Backend API<br/><br/>PHP<br/>REST Services<br/>Business Logic")

end


subgraph INTELLIGENCE["AI Intelligence Layer"]

FASTAPI("Python FastAPI<br/><br/>AI Processing")

LLM("Large Language Models<br/><br/>Career Analysis<br/>Recommendations")

end


subgraph DATA["Data Layer"]

MYSQL("MySQL 8.x<br/><br/>Application Database")

REDIS("Redis<br/><br/>Cache<br/>Queue Management")

end


subgraph CLOUD["Cloud Layer"]

AWS("AWS Infrastructure<br/><br/>Storage<br/>Monitoring<br/>Deployment")

end



USER --> ANGULAR

ANGULAR --> LARAVEL

LARAVEL --> FASTAPI

FASTAPI --> LLM

LARAVEL --> MYSQL

LARAVEL --> REDIS

LARAVEL --> AWS



classDef user fill:#334155,stroke:#CBD5E1,color:#FFFFFF;

classDef frontend fill:#2563EB,stroke:#93C5FD,color:#FFFFFF;

classDef backend fill:#7C3AED,stroke:#C4B5FD,color:#FFFFFF;

classDef intelligence fill:#D97706,stroke:#FCD34D,color:#FFFFFF;

classDef data fill:#059669,stroke:#6EE7B7,color:#FFFFFF;

classDef cloud fill:#0891B2,stroke:#67E8F9,color:#FFFFFF;



class USER user;

class ANGULAR frontend;

class LARAVEL backend;

class FASTAPI,LLM intelligence;

class MYSQL,REDIS data;

class AWS cloud;

```

---

# Architecture Explanation


## Presentation Layer

Responsible for:

- User interface
- Dashboard visualization
- Resume upload
- Career analytics


Technology:

```
Angular
TypeScript
Tailwind CSS
```


---

## Application Layer


Responsible for:

- Authentication
- Business logic
- API management
- User management
- Database communication


Technology:

```
Laravel
PHP
REST API
```


---

## AI Intelligence Layer


Responsible for:

- Resume analysis
- Skill extraction
- Career recommendations
- Interview evaluation


Technology:

```
Python
FastAPI
LLM Models
```


---

## Data Layer


Responsible for:

- Persistent storage
- Caching
- Background processing


Technology:

```
MySQL
Redis
```


---

# 4. Frontend Architecture


## 4.1 Technology Stack


| Technology | Purpose |
|-|-|
| Angular | Frontend Framework |
| TypeScript | Programming Language |
| Tailwind CSS | Styling |
| Angular Material | UI Components |


---

## 4.2 Frontend Responsibilities


The frontend manages:


- User interaction
- Dashboard rendering
- Resume upload interface
- Career visualization
- API communication


---

## 4.3 Angular Module Architecture


```mermaid
%%{init:{
'theme':'base',
'themeVariables':{
'fontFamily':'Inter',
'lineColor':'#94A3B8'
}
}}%%


flowchart TB


APP("Angular Application")


AUTH("Authentication Module")

PROFILE("Career Profile Module")

RESUME("Resume Intelligence Module")

DASH("Career Dashboard")

ROADMAP("Learning Roadmap")

SKILL("Skill Management")



APP --> AUTH

APP --> PROFILE

APP --> RESUME

APP --> DASH

APP --> ROADMAP

APP --> SKILL



classDef frontend fill:#2563EB,stroke:#93C5FD,color:#FFFFFF;


class APP frontend;

class AUTH,PROFILE,RESUME,DASH,ROADMAP,SKILL frontend;

```

---

# 5. Backend Architecture


## 5.1 Technology Stack


| Technology | Purpose |
|-|-|
| Laravel | Backend Framework |
| PHP | Programming Language |
| REST API | Communication |
| Laravel Sanctum | Authentication |
| Laravel Queue | Background Jobs |


---

## 5.2 Backend Responsibilities


Laravel handles:


- Authentication
- Authorization
- Business logic
- Database operations
- API endpoints
- Background processing


---

## 5.3 Laravel Internal Architecture


```mermaid
%%{init:{
'theme':'base',
'themeVariables':{
'fontFamily':'Inter',
'lineColor':'#94A3B8'
}
}}%%


flowchart TB


API("REST API")


CONTROLLER("Controllers")


SERVICE("Service Layer")


REPOSITORY("Repository Layer")


MODEL("Eloquent Models")


DATABASE("MySQL Database")



API --> CONTROLLER

CONTROLLER --> SERVICE

SERVICE --> REPOSITORY

REPOSITORY --> MODEL

MODEL --> DATABASE



classDef backend fill:#7C3AED,stroke:#C4B5FD,color:#FFFFFF;

classDef data fill:#059669,stroke:#6EE7B7,color:#FFFFFF;


class API,CONTROLLER,SERVICE,REPOSITORY,MODEL backend;

class DATABASE data;

```

---

**End of Part 1/3**

I will provide **Part 2/3** next:
- AI Intelligence Architecture
- AI processing pipeline
- Database architecture
- ER diagram
- Redis queue architecture

Then **Part 3/3**:
- Docker architecture
- AWS deployment
- Security
- CI/CD
- Scalability
- Technology decisions
---

# 6. AI Intelligence Architecture


## 6.1 AI Service Design


CareerIQ AI separates artificial intelligence workloads from the main Laravel application.


This approach provides:


- Independent scaling
- Easier AI model replacement
- Better resource management
- Faster AI development cycle


---

## 6.2 AI Technology Stack


| Technology | Purpose |
|-|-|
| Python | AI Development |
| FastAPI | AI Service API |
| NLP Models | Text Processing |
| LLM APIs | Intelligent Recommendations |
| Machine Learning Models | Prediction and Analysis |


---

## 6.3 AI Service Architecture


```mermaid
%%{init:{
'theme':'base',
'themeVariables':{
'fontFamily':'Inter',
'lineColor':'#94A3B8'
}
}}%%


flowchart TB


LARAVEL("Laravel Backend<br/><br/>Request AI Analysis")


FASTAPI("Python FastAPI Service<br/><br/>AI Processing Layer")


PARSER("Resume Parser<br/><br/>Text Extraction")


NLP("NLP Engine<br/><br/>Skill Identification")


MODEL("Recommendation Engine<br/><br/>Career Intelligence")


LLM("Large Language Model<br/><br/>AI Generated Insights")


RESULT("Career Report<br/><br/>Recommendations<br/>Roadmap")



LARAVEL --> FASTAPI

FASTAPI --> PARSER

PARSER --> NLP

NLP --> MODEL

MODEL --> LLM

LLM --> RESULT



classDef backend fill:#7C3AED,stroke:#C4B5FD,color:#FFFFFF;

classDef ai fill:#D97706,stroke:#FCD34D,color:#FFFFFF;

classDef output fill:#0891B2,stroke:#67E8F9,color:#FFFFFF;



class LARAVEL backend;

class FASTAPI,PARSER,NLP,MODEL,LLM ai;

class RESULT output;

```

---

# 6.4 AI Resume Analysis Workflow


The resume analysis process follows these steps:


```mermaid
sequenceDiagram


participant User

participant Angular

participant Laravel

participant AI as FastAPI Service

participant Model as AI Model

participant MySQL



User->>Angular: Upload Resume PDF

Angular->>Laravel: Send Resume File

Laravel->>MySQL: Store Resume Metadata

Laravel->>AI: Request Analysis

AI->>AI: Extract Text

AI->>AI: Identify Skills

AI->>Model: Generate Career Insights

Model-->>AI: Return Recommendations

AI-->>Laravel: Send Analysis Result

Laravel->>MySQL: Save Results

Laravel-->>Angular: Display Insights

Angular-->>User: Show Career Report

```

---

# 7. Database Architecture


## 7.1 Database Overview


CareerIQ AI uses a relational database architecture.


Technology:


```
MySQL 8.x

+

InnoDB Storage Engine

+

Laravel Eloquent ORM

```


---

# 7.2 Database Responsibilities


The database manages:


- User accounts
- Career profiles
- Education records
- Professional experience
- Technical skills
- Projects
- Resumes
- Career goals
- Learning progress
- AI analysis results


---

# 7.3 Database Design Principles


The database follows:


## Normalization

Reducing duplicate data and maintaining consistency.


## Indexing

Improving query performance for:


- User search
- Skill lookup
- Career matching


## Relationships

Maintaining:

- One-to-many relationships
- Many-to-many relationships
- Foreign key constraints


---

# 7.4 Entity Relationship Diagram


```mermaid
%%{init:{
'theme':'base',
'themeVariables':{
'fontFamily':'Inter'
}
}}%%


erDiagram


USER ||--o{ RESUME : uploads

USER ||--o{ PROJECT : creates

USER ||--o{ EXPERIENCE : has

USER ||--o{ USER_SKILL : owns

SKILL ||--o{ USER_SKILL : contains

USER ||--o{ CAREER_GOAL : selects

CAREER_GOAL ||--o{ LEARNING_ROADMAP : generates

RESUME ||--o{ AI_ANALYSIS : produces



USER {

INT id PK

VARCHAR name

VARCHAR email

VARCHAR password

DATETIME created_at

}



RESUME {

INT id PK

INT user_id FK

VARCHAR file_path

DATETIME uploaded_at

}



PROJECT {

INT id PK

INT user_id FK

VARCHAR title

TEXT description

}



EXPERIENCE {

INT id PK

INT user_id FK

VARCHAR company

VARCHAR position

}



SKILL {

INT id PK

VARCHAR name

VARCHAR category

}



USER_SKILL {

INT id PK

INT user_id FK

INT skill_id FK

VARCHAR level

}



CAREER_GOAL {

INT id PK

VARCHAR title

TEXT description

}



LEARNING_ROADMAP {

INT id PK

INT career_goal_id FK

TEXT roadmap

}



AI_ANALYSIS {

INT id PK

INT resume_id FK

TEXT result

}

```

---

# 7.5 Database Access Architecture


The application communicates with MySQL through Laravel's ORM layer.


```mermaid
%%{init:{
'theme':'base',
'themeVariables':{
'fontFamily':'Inter',
'lineColor':'#94A3B8'
}
}}%%


flowchart LR


APPLICATION("Laravel Application")


ORM("Eloquent ORM")


QUERY("SQL Query Layer")


MYSQL("MySQL Database")



APPLICATION --> ORM

ORM --> QUERY

QUERY --> MYSQL



classDef backend fill:#7C3AED,stroke:#C4B5FD,color:#FFFFFF;

classDef database fill:#059669,stroke:#6EE7B7,color:#FFFFFF;



class APPLICATION,ORM,QUERY backend;

class MYSQL database;

```

---

# 8. Redis Cache and Queue Architecture


## 8.1 Purpose of Redis


Redis improves system performance by handling:


### Cache Layer

Stores:


- Frequently accessed career recommendations
- Skill information
- Dashboard statistics


### Queue Layer

Handles:


- Resume processing
- AI analysis tasks
- Background reports


---

# 8.2 Redis Processing Flow


```mermaid
%%{init:{
'theme':'base',
'themeVariables':{
'fontFamily':'Inter',
'lineColor':'#94A3B8'
}
}}%%


flowchart LR


REQUEST("User Request")


API("Laravel API")


JOB("Background Job")


REDIS("Redis Queue")


WORKER("Queue Worker")


AI("AI Processing")


RESULT("Stored Result")



REQUEST --> API

API --> JOB

JOB --> REDIS

REDIS --> WORKER

WORKER --> AI

AI --> RESULT



classDef backend fill:#7C3AED,stroke:#C4B5FD,color:#FFFFFF;

classDef database fill:#059669,stroke:#6EE7B7,color:#FFFFFF;

classDef ai fill:#D97706,stroke:#FCD34D,color:#FFFFFF;

classDef output fill:#0891B2,stroke:#67E8F9,color:#FFFFFF;



class API,JOB,WORKER backend;

class REDIS database;

class AI ai;

class RESULT output;

```

---

# 9. Data Flow Summary


The complete data lifecycle:


```mermaid
%%{init:{
'theme':'base',
'themeVariables':{
'fontFamily':'Inter',
'lineColor':'#94A3B8'
}
}}%%


flowchart TB


USER("User")


FRONTEND("Angular")


BACKEND("Laravel")


DATABASE("MySQL")


AI("AI Engine")


INSIGHT("Career Insights")



USER --> FRONTEND

FRONTEND --> BACKEND

BACKEND --> DATABASE

BACKEND --> AI

AI --> DATABASE

DATABASE --> BACKEND

BACKEND --> FRONTEND

FRONTEND --> INSIGHT



classDef user fill:#334155,stroke:#CBD5E1,color:#FFFFFF;

classDef frontend fill:#2563EB,stroke:#93C5FD,color:#FFFFFF;

classDef backend fill:#7C3AED,stroke:#C4B5FD,color:#FFFFFF;

classDef data fill:#059669,stroke:#6EE7B7,color:#FFFFFF;

classDef ai fill:#D97706,stroke:#FCD34D,color:#FFFFFF;

classDef output fill:#0891B2,stroke:#67E8F9,color:#FFFFFF;



class USER user;

class FRONTEND frontend;

class BACKEND backend;

class DATABASE data;

class AI ai;

class INSIGHT output;

```

---

**End of Part 2/3**

Next Part 3/3 will contain:

- Docker container architecture
- AWS production architecture
- Security architecture
- CI/CD pipeline
- Scalability strategy
- Future architecture evolution
- Technology decisions table
- Final conclusion
---

# 10. Infrastructure Architecture


## 10.1 Docker Container Strategy


CareerIQ AI uses Docker to provide:


- Environment consistency
- Service isolation
- Easier deployment
- Cloud readiness
- Simplified development workflow


Each major service runs inside an independent container.


---

# 10.2 Container Architecture


```mermaid
%%{init:{
'theme':'base',
'themeVariables':{
'fontFamily':'Inter',
'lineColor':'#94A3B8'
}
}}%%


flowchart TB


DOCKER("Docker Environment")


FRONTEND("Angular Container<br/><br/>Node.js Runtime")


BACKEND("Laravel Container<br/><br/>PHP Runtime")


AI("AI Service Container<br/><br/>Python Runtime")


DATABASE("MySQL Container<br/><br/>Database Service")


CACHE("Redis Container<br/><br/>Cache Service")



DOCKER --> FRONTEND

DOCKER --> BACKEND

DOCKER --> AI

DOCKER --> DATABASE

DOCKER --> CACHE



classDef infrastructure fill:#0891B2,stroke:#67E8F9,color:#FFFFFF;

classDef frontend fill:#2563EB,stroke:#93C5FD,color:#FFFFFF;

classDef backend fill:#7C3AED,stroke:#C4B5FD,color:#FFFFFF;

classDef ai fill:#D97706,stroke:#FCD34D,color:#FFFFFF;

classDef database fill:#059669,stroke:#6EE7B7,color:#FFFFFF;



class DOCKER infrastructure;

class FRONTEND frontend;

class BACKEND backend;

class AI ai;

class DATABASE,CACHE database;

```

---

# 11. Cloud Deployment Architecture


## 11.1 AWS Production Design


CareerIQ AI is designed for deployment on AWS cloud infrastructure.


The production architecture includes:


| AWS Service | Purpose |
|-|-|
| Route 53 | Domain management |
| CloudFront | Content delivery |
| Load Balancer | Traffic distribution |
| ECS / EC2 | Application hosting |
| RDS | Managed MySQL database |
| ElastiCache | Redis caching |
| S3 | File storage |
| CloudWatch | Monitoring |


---

# 11.2 AWS Architecture Diagram


```mermaid
%%{init:{
'theme':'base',
'themeVariables':{
'fontFamily':'Inter',
'lineColor':'#94A3B8'
}
}}%%


flowchart TB


USERS("Global Users")


ROUTE53("AWS Route 53")


CLOUDFRONT("CloudFront CDN")


ALB("Application Load Balancer")



subgraph AWS["AWS Cloud Environment"]


APP("Laravel Application<br/><br/>EC2 / ECS")


AI("AI Service<br/><br/>FastAPI")


RDS("Amazon RDS<br/><br/>MySQL")


CACHE("ElastiCache<br/><br/>Redis")


S3("Amazon S3<br/><br/>Resume Storage")


MONITOR("CloudWatch<br/><br/>Monitoring")


end



USERS --> ROUTE53

ROUTE53 --> CLOUDFRONT

CLOUDFRONT --> ALB

ALB --> APP


APP --> AI

APP --> RDS

APP --> CACHE

APP --> S3

APP --> MONITOR



classDef cloud fill:#0891B2,stroke:#67E8F9,color:#FFFFFF;

classDef backend fill:#7C3AED,stroke:#C4B5FD,color:#FFFFFF;

classDef ai fill:#D97706,stroke:#FCD34D,color:#FFFFFF;

classDef database fill:#059669,stroke:#6EE7B7,color:#FFFFFF;


class ROUTE53,CLOUDFRONT,ALB cloud;

class APP backend;

class AI ai;

class RDS,CACHE database;

class S3,MONITOR cloud;

```

---

# 12. Security Architecture


## 12.1 Security Strategy


Security is implemented across every layer of the system.


---

## Application Security


Implemented using:


- Authentication
- Authorization
- Input validation
- Secure API communication
- OWASP security practices


---

## Database Security


Implemented through:


- Secure credentials
- Prepared statements
- Role-based access
- Backup policies


---

## Cloud Security


Implemented through:


- AWS IAM
- Security Groups
- HTTPS certificates
- Network isolation


---

# 12.2 Security Flow


```mermaid
%%{init:{
'theme':'base',
'themeVariables':{
'fontFamily':'Inter',
'lineColor':'#94A3B8'
}
}}%%


flowchart LR


USER("User")


AUTH("Authentication Layer")


API("Protected API")


SECURITY("Security Controls")


DATABASE("Protected Database")



USER --> AUTH

AUTH --> API

API --> SECURITY

SECURITY --> DATABASE



classDef user fill:#334155,stroke:#CBD5E1,color:#FFFFFF;

classDef security fill:#BE123C,stroke:#FB7185,color:#FFFFFF;

classDef database fill:#059669,stroke:#6EE7B7,color:#FFFFFF;



class USER user;

class AUTH,API,SECURITY security;

class DATABASE database;

```

---

# 13. CI/CD Architecture


## 13.1 Development Pipeline


CareerIQ AI follows an automated CI/CD workflow.


Pipeline stages:


1. Code Development
2. Version Control
3. Automated Testing
4. Docker Build
5. Deployment


---

# 13.2 CI/CD Pipeline Diagram


```mermaid
%%{init:{
'theme':'base',
'themeVariables':{
'fontFamily':'Inter',
'lineColor':'#94A3B8'
}
}}%%


flowchart LR


DEVELOPER("Developer")


GITHUB("GitHub Repository")


ACTION("GitHub Actions")


TEST("Automated Testing")


BUILD("Docker Build")


DEPLOY("AWS Deployment")



DEVELOPER --> GITHUB

GITHUB --> ACTION

ACTION --> TEST

TEST --> BUILD

BUILD --> DEPLOY



classDef pipeline fill:#2563EB,stroke:#93C5FD,color:#FFFFFF;


class DEVELOPER,GITHUB,ACTION,TEST,BUILD,DEPLOY pipeline;

```

---

# 14. Scalability Strategy


CareerIQ AI is designed to grow from a single deployment into a large-scale platform.


---

## Current Architecture


```
Modular Laravel Backend

+

Independent AI Service

+

Relational Database

```


---

## Future Scaling Improvements


## Application Scaling

Future improvements:


- Multiple backend instances
- Load balancing
- Auto scaling


---

## Database Scaling


Future improvements:


- Query optimization
- Advanced indexing
- Read replicas
- Database clustering


---

## AI Scaling


Future improvements:


- Dedicated AI workers
- GPU acceleration
- Model optimization
- Vector database integration


---

## Infrastructure Scaling


Future improvements:


- Kubernetes deployment
- Microservice architecture
- Event-driven processing


---

# 15. Future Architecture Evolution


CareerIQ AI can evolve from a modular platform into a highly scalable AI ecosystem.


```mermaid
%%{init:{
'theme':'base',
'themeVariables':{
'fontFamily':'Inter',
'lineColor':'#94A3B8'
}
}}%%


flowchart LR


CURRENT("Current System<br/><br/>Laravel + AI Service")


NEXT("Future Platform<br/><br/>Microservices")


ADVANCED("Advanced AI Platform<br/><br/>Kubernetes<br/>Vector Database<br/>AI Infrastructure")



CURRENT --> NEXT

NEXT --> ADVANCED



classDef backend fill:#7C3AED,stroke:#C4B5FD,color:#FFFFFF;

classDef future fill:#D97706,stroke:#FCD34D,color:#FFFFFF;



class CURRENT,NEXT backend;

class ADVANCED future;

```

---

# 16. Technology Decisions


| Technology | Reason |
|-|-|
| Angular | Enterprise frontend framework with strong TypeScript support |
| Laravel | Mature PHP ecosystem and rapid backend development |
| MySQL 8.x | Reliable relational database with strong transactional support |
| FastAPI | Lightweight and scalable AI service framework |
| Redis | High-performance caching and background processing |
| Docker | Consistent development and deployment environments |
| GitHub Actions | Automated CI/CD workflow |
| AWS | Production-ready cloud infrastructure |
| Terraform | Infrastructure as Code automation |


---

# 17. Final Architecture Summary


CareerIQ AI architecture provides:


## Maintainability

Through:

- Modular design
- Clear separation of responsibilities
- Documented architecture


## Scalability

Through:

- Independent AI services
- Cloud deployment
- Containerization


## Reliability

Through:

- Automated testing
- CI/CD pipeline
- Monitoring


## Intelligence

Through:

- AI-powered analysis
- Recommendation systems
- Data-driven career insights


---

# End of Document