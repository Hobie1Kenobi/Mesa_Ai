# MESA Rights Vault - System Architecture

## System Components and Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           MESA RIGHTS VAULT                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION LAYER                          │
│                                                                         │
│  ┌───────────────┐      ┌───────────────┐      ┌───────────────┐       │
│  │  Rights Input │      │Privacy Controls│      │ Verification  │       │
│  │   Interface   │◄────►│  Management   │◄────►│   Interface   │       │
│  └───────────────┘      └───────────────┘      └───────────────┘       │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           CORE SERVICES LAYER                           │
│                                                                         │
│  ┌───────────────┐      ┌───────────────┐      ┌───────────────┐       │
│  │ AI Guardian   │      │  ZK Proof     │      │  MusicBrainz  │       │
│  │ (Data Extract)│◄────►│   System      │◄────►│  Integration  │       │
│  └───────────────┘      └───────────────┘      └───────────────┘       │
│                                │                                        │
│                                ▼                                        │
│  ┌───────────────┐      ┌───────────────┐      ┌───────────────┐       │
│  │ Privacy Layer │      │ Rights Manager│      │Selective Discl│       │
│  │  Encryption   │◄────►│    Service    │◄────►│    Service    │       │
│  └───────────────┘      └───────────────┘      └───────────────┘       │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        BLOCKCHAIN STORAGE LAYER                         │
│                                                                         │
│  ┌───────────────┐      ┌───────────────┐      ┌───────────────┐       │
│  │  RightsVault  │      │ MusicRights   │      │ Verification  │       │
│  │    Contract   │◄────►│    Vault      │◄────►│   Registry    │       │
│  └───────────────┘      └───────────────┘      └───────────────┘       │
│                                                                         │
│                        BASE SEPOLIA BLOCKCHAIN                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Process

1. **Rights Registration Flow**

```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐     ┌───────────────┐
│              │     │               │     │              │     │               │
│  Music Right ├────►│  AI Guardian  ├────►│ Privacy Layer├────►│  Rights Vault │
│   Document   │     │  Extraction   │     │  Encryption  │     │   Contract    │
│              │     │               │     │              │     │               │
└──────────────┘     └───────────────┘     └──────────────┘     └───────────────┘
```

2. **Verification Flow**

```
┌────────────┐    ┌──────────────┐    ┌───────────────┐    ┌───────────────┐
│            │    │              │    │               │    │               │
│  Rights ID ├───►│  ZK Proof    ├───►│ Verification  ├───►│  Verification │
│  Request   │    │  Generation  │    │    Check      │    │    Result     │
│            │    │              │    │               │    │               │
└────────────┘    └──────────────┘    └───────────────┘    └───────────────┘
```

3. **MusicBrainz Integration Flow**

```
┌────────────┐    ┌──────────────┐    ┌───────────────┐    ┌───────────────┐
│            │    │              │    │               │    │               │
│  Music     ├───►│  MusicBrainz ├───►│  Map to MESA  ├───►│ Store Hashed  │
│  Metadata  │    │   Lookup     │    │  Rights Model │    │  Reference    │
│            │    │              │    │               │    │               │
└────────────┘    └──────────────┘    └───────────────┘    └───────────────┘
```

4. **Selective Disclosure Flow**

```
┌────────────┐    ┌──────────────┐    ┌───────────────┐    ┌───────────────┐
│            │    │              │    │               │    │               │
│ Rights Data├───►│ Field Select ├───►│ ZK Proof Gen  ├───►│ Disclosure    │
│            │    │ + Policies   │    │ for Selected  │    │ Package       │
│            │    │              │    │               │    │               │
└────────────┘    └──────────────┘    └───────────────┘    └───────────────┘
```

## System Components Explained

### User Interaction Layer

- **Rights Input Interface**: Where users upload or input their music rights data
- **Privacy Controls Management**: Interface for setting what data is public/private
- **Verification Interface**: Where users can generate/verify proofs

### Core Services Layer

- **AI Guardian**: Extracts structured data from rights documents
- **ZK Proof System**: Generates and verifies zero-knowledge proofs
- **MusicBrainz Integration**: Connects to MusicBrainz database
- **Privacy Layer**: Handles encryption and data protection
- **Rights Manager Service**: Orchestrates rights data operations
- **Selective Disclosure Service**: Controls what data is shared with whom

### Blockchain Storage Layer

- **RightsVault Contract**: Stores encrypted rights data
- **MusicRightsVault**: Music-specific rights management
- **Verification Registry**: Records verification status

## Implementation Notes

- All components use privacy-by-design principles
- Data is encrypted before being stored on-chain
- Zero-knowledge proofs allow verification without revealing sensitive data
- The system uses Base Sepolia for reduced gas costs and Ethereum compatibility
- MusicBrainz integration provides industry-standard identification 