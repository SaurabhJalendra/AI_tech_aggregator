# Module Specification Guide

## Adding a New Module

### 1. Create the YAML Spec

Create a file `modules_registry/specs/{slug}.yaml` following the schema at `modules_registry/schema.yaml`.

### 2. Required Sections

Every spec must include:

- **meta** — slug, name, category, status
- **identity** — tagline, description, links
- **capabilities** — use cases, operations, integrations
- **comparison_dimensions** — 8 dimensions scored 1-10
- **knowledge** — at least 1 expert-level knowledge entry

### 3. Validate

```bash
# Run the spec validation test
cd backend && pytest tests/test_module_loader.py::test_all_spec_files_are_valid_yaml -v
```

### 4. Load into Database

```bash
cd backend && python ../scripts/seed_db.py
```

### 5. Auto-Generate with AI

```bash
# List pending modules
python scripts/generate_module.py --list

# Generate one module
python scripts/generate_module.py weaviate

# Generate all in a category
python scripts/generate_module.py --batch vector_databases

# Generate all remaining
python scripts/generate_module.py --all
```

## Categories

| Slug | Name | Pipeline Stage |
|------|------|---------------|
| data_ingestion | Data Ingestion & Preparation | Input |
| chunking | Chunking & Segmentation | Processing |
| embeddings | Embeddings & Representation | Processing |
| vector_databases | Vector Storage & Indexing | Storage |
| retrieval | Retrieval & Search | Query |
| rag_architectures | RAG Architectures | Pattern |
| llm_layer | LLM Layer | Generation |
| agent_systems | Agent Systems | Orchestration |
| evaluation | Evaluation & Quality | Testing |
| caching | Caching & Optimization | Performance |
| fine_tuning | Fine-Tuning & Customization | Training |
| deployment | Deployment & Operations | Infrastructure |
| voice_conversational | Voice & Conversational | Interface |
| workflow_orchestration | Workflow & Orchestration | Orchestration |
| security_compliance | Security & Compliance | Governance |
| search_discovery | Search & Discovery | Query |
| specialized_applications | Specialized Applications | Domain |
| infrastructure_comparison | Infrastructure Comparison | Meta |

## Comparison Dimensions

Each module is scored on 8 dimensions (1-10):

1. **performance** — Speed, throughput, latency
2. **scalability** — Horizontal/vertical scaling capability
3. **ease_of_use** — Developer experience, documentation quality
4. **cost_efficiency** — Total cost of ownership
5. **community** — Community size, ecosystem richness
6. **maturity** — Production readiness, battle-tested
7. **flexibility** — Customization and extensibility
8. **data_privacy** — Data sovereignty, on-prem options
