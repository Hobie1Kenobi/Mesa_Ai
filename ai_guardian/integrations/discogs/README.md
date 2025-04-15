# Discogs Integration for MESA Rights Vault

This module provides a connector between the MESA Rights Vault system and Discogs, allowing the AI agent to retrieve and integrate music metadata while maintaining privacy-preserving features.

## Overview

The integration allows the MESA Rights Vault system to:

1. Search and retrieve metadata from Discogs
2. Map Discogs data to the MESA Rights schema
3. Store and cache data for efficient retrieval
4. Apply privacy-preserving techniques to sensitive data
5. Generate zero-knowledge proofs for rights verification

## Components

### DiscogsConnector

The main interface to the Discogs API, handling:
- Authentication and rate limiting
- Data mapping between schemas
- Privacy-preserving data handling
- Zero-knowledge proof generation

### DiscogsDatabase

A SQLite-based database for:
- Caching Discogs metadata
- Storing mappings to MESA rights data
- Tracking API usage for rate limiting
- Caching AI agent queries

### DiscogsAIAgent

An interface for the AI agent to interact with Discogs data, providing:
- Natural language query processing
- Rights verification
- Metadata lookup
- Royalty calculation

## Setup

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Create configuration file:
Create a `discogs_config.json` file with the following structure:
```json
{
  "user_token": "YOUR_DISCOGS_API_TOKEN",
  "user_agent": "MESA Rights Vault/1.0 +https://yourwebsite.com",
  "encryption_key": "YOUR_ENCRYPTION_KEY"
}
```

3. Initialize the database:
```python
from discogs_database import DiscogsDatabase
db = DiscogsDatabase()
```

## Usage

### Basic Search

```python
from discogs_connector import DiscogsConnector

connector = DiscogsConnector()
results = connector.find_rights_metadata({"title": "Bohemian Rhapsody", "artist": "Queen"})
```

### AI Agent Interface

```python
from ai_agent_interface import DiscogsAIAgent

agent = DiscogsAIAgent()
result = agent.process_query("Who owns the rights to 'Bohemian Rhapsody' by Queen?")
```

### Verify Rights

```python
proof = agent.verify_rights_claim("right_id_123", "ownership")
```

## Privacy Features

This integration implements several privacy-preserving features:

1. **Encryption**: Sensitive data is encrypted before storage
2. **Zero-Knowledge Proofs**: Rights verification without revealing data
3. **Selective Disclosure**: Control which fields are public vs. private
4. **Hashed References**: Entity IDs are stored as secure hashes

## Schema Mapping

The `discogs_schema.json` file defines how Discogs data maps to the MESA Rights Vault schema, including:

- Entity definitions (Release, Artist, Label)
- Field mappings between schemas
- Data validation rules

## License

This module is part of the MESA Rights Vault system and is licensed under the same terms as the main project. 