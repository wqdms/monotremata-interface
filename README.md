# monotremata-interface

A backend that creates new djabgo project based on preset templates and configuration.
Following entity–attribute–value model (EAV) concept to buld a backand around existing data like csv, xlmx or database schemas.
EAV is a data model optimized for the space-efficient storage of sparse—or ad-hoc—property or data values, intended for situations 
where runtime usage patterns are arbitrary, subject to user variation, or otherwise unforeseeable using a fixed design.

## Use Case: Water Quality Management System

### The Problem

- **Proprietary systems** run under high license fees and are not developer-friendly
- **Fragmented datasets** bring new specifications with each new participant
- **Individual configurations** vary per stakeholder, creating complexity
- **Low budgets and limited infrastructure** constrain open-source adoption
- Data ownership and privacy concerns compound the challenge

### Requirements

|                          |                             |
|--------------------------|-----------------------------|
| Best practices for software development | Integrate stakeholder & compliance requirements |
| Geoinformation standards (OGC, GEOS) | Decentralized architecture                         |
| Maintainable             | Cross-platform operation                                       |
| Increase interoperability with other systems |                                            |

## Iteration Journey (what happend since last year 2025)

### Initial Phase

- Searched for available solutions, standards, and best practices

- Planned testing phase

- Searched most valued use cases for water quality data management system
  
  - **GEMS/Stat**

  - **SDG632**

  - **SensorThings**

  - **HydroSHEDS**


### Testing Phase

- Cluster setup to run tests on open-source software

- Collected solutions and analyzed dependencies

### Experimental Phase

- Wrote PyPI packages 
  
  - https://pypi.org/project/django-sensorthings/

  - https://pypi.org/project/django-hydrosheds/

  - https://pypi.org/project/django-ct-ontology/

- Processed datasets

### Conclusion Phase

- **Recognized bottlenecks:** development process is highly inefficient for single organizations

- **Recurring problems needed automation**
  
  - Versioning and setup of code base
  
  - Individual configuration based on environment
  
  - Reusable code templates, dependencies, documentation, standards, and processes

## The Solution

Decompose complexity into simple chunks, then reorganize and bundle:


1. **Decompose** — Break `Complicated → Complex → Simple Chunks`

2. **Generate** — Build backends from data schemas (user-defined)

3. **Integrate** — Base functionality around a `Deployment` model

4. **Autonomy** — Versioning independent of any platform; zip-based deployment options

> *"Write a system that writes a system"*

### Optional AI Integration

- MCP server communicates with OpenAPI REST framework

- Backend hosts `flatpages` for user-defined instructions and documentation

## Key Experiences

1. It is hard to run, maintain, and future-proof systems from scratch
2. Open source reuse pays off with proper preparation
3. Do not solve every problem in one application — split into chunks
4. Allow modifications and extensions in real time
5. Enable multiple user interfaces, split into smaller independent chunks
6. Maintain one parent backend as the blueprint for future child backends

**make Complicated → make Complex → structure to Simple Chunks → reorganize to Complex → Bundle**

## What it does

Monotremata is a **Django CMS engine** that generates full Django web applications from declarative schema definitions. It uses an Entity–Attribute–Value (EAV) model to build backends around existing data — CSV, XML, XLSX, or database schemas — supporting arbitrary/unknown property structures at runtime.

## Architecture

```
Organization
  └── Project          (db_driver, category, owner, members)
        └── Application (template_string/url/file, render_from, context)
      └── Domain        (metadata namespace)
      └── Namespace
      └── Deployment
```

## Core API resources

| Endpoint | Purpose |
|---|---|
| `GET /organization/` | Top-level org container |
| `GET /project/` | Projects with apps and domain config |
| `GET /application/` | Application definitions |
| `GET /domain/` | Logical grouping / metadata |
| `GET /namespace/` | Namespaces tied to domains |
| `GET /presetmodel/` | Declarative model definitions (className, classParent, fields) |
| `GET /presetmodelfield/` | Model fields (charField, booleanField, JSONField, GeometryField, etc.) |
| `GET /deployment/` | Deploy records (auth required) |

## Download Zip

You can download your configuration as zip folder either as complete ornaization folder or as standalone module

- organization folder including

- django-projects

- django-applications

download url usage with parameter `?format=download`

- at `/application`

- or `/project`

- or `/organization` level.

## The `presetmodel` model

The key primitive: a declarative model definition that lists:

- **className** / **classParent** — Django model class name and parent (e.g. `Domain` → `models.Model`)
- **fields** — list of fields with `fieldName`, `fieldDataType` (CharField, JSONField, PointField, etc.)
- **is_abstract**, **ordering_list**, **serializerClassParent**, **viewsetClassParent**

From a PresetModel, Monotremata generates:

0. Django Project

1. Django models and ORM

2. Serializers (ModelSerializer)

3. ViewSets (ModelViewSet)

4. rest api routes (DefaultRouter)

5. OpenAPI specification (swagger)

6. Unit tests

## The `Deployment` model

Contains configuration to deploy a specific project by given credentials.
It produces necessary scripts to setup the generated code base to run the
new backend.

**Provided scripts**

0. cli.sh
1. argocd applicationset.yaml
2. Dockerfile
3. docker-compose.yaml

**Automated Git Api**

can create and manage git:

- organizations

- repositories

## Management commands

```
uv run manage setup -s

uv run manage setup -s run

uv run manage git

uv run manage parser
```

## Integrations

- REST API and OpenAPI specification
- JWT auth
- Geographic Information System (GIS)
- Database Engines
- Flatpages
- Management commands
- Templating System
- Test Framework
- Data Import Export multiple formats
- Document & Downloads
- Jupyter Notebooks (visualization and data analysis, coming soon)
- Shell Environment (`shell_plus`, plugins coming soon)
- AI Capabilities (MCP coming soon)
- see `pyproject.toml`, `settings.INSTALLED_APPS` and `Dockerfile` for more integrations

## Why it matters

It lets you spin up a fully functional Django REST API with admin panel from a JSON-schema, without writing any Django code — the EAV model handles the sparsity of ad-hoc / user-defined data structures that fixed schemas can't.
