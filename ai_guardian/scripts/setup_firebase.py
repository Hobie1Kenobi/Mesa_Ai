#!/usr/bin/env python3

import os
import json
import shutil

# Base directory where Firebase files will be created
BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "firebase-config")

# File content definitions
FILE_CONTENTS = {
    "firebase.json": """{
  "firestore": {
    "rules": "firestore.rules",
    "indexes": "firestore.indexes.json"
  },
  "functions": {
    "predeploy": [
      "npm --prefix \\"$RESOURCE_DIR\\" run lint",
      "npm --prefix \\"$RESOURCE_DIR\\" run build"
    ],
    "source": "functions"
  },
  "hosting": {
    "public": "public",
    "rewrites": [
      {
        "source": "/api/**",
        "function": "api"
      },
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ]
  },
  "storage": {
    "rules": "storage.rules"
  },
  "emulators": {
    "auth": {
      "port": 9099
    },
    "functions": {
      "port": 5001
    },
    "firestore": {
      "port": 8080
    },
    "hosting": {
      "port": 5000
    },
    "storage": {
      "port": 9199
    },
    "ui": {
      "enabled": true
    }
  },
  "remoteconfig": {
    "template": "remoteconfig.template.json"
  }
}""",

    "firestore.rules": """rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Rights data - only accessible by owner or with explicit permission
    match /rights/{rightId} {
      // Allow read if user is the owner
      allow read: if request.auth != null && 
                   (resource.data.ownerId == request.auth.uid ||
                    exists(/databases/$(database)/documents/permissions/$(rightId)/users/$(request.auth.uid)));
      
      // Allow write only if user is the owner
      allow write: if request.auth != null && resource.data.ownerId == request.auth.uid;
      
      // Rights metadata collection - public but limited information
      match /metadata/{metadataId} {
        allow read: if true;
        allow write: if request.auth != null && get(/databases/$(database)/documents/rights/$(rightId)).data.ownerId == request.auth.uid;
      }
    }
    
    // User profiles
    match /users/{userId} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if request.auth != null && request.auth.uid == userId;
      
      // User's public profile
      match /public/{document=**} {
        allow read: if true;
        allow write: if request.auth != null && request.auth.uid == userId;
      }
    }
    
    // Permissions for shared rights
    match /permissions/{rightId}/users/{userId} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if request.auth != null && 
                   get(/databases/$(database)/documents/rights/$(rightId)).data.ownerId == request.auth.uid;
    }
    
    // Verification records
    match /verifications/{verificationId} {
      allow read: if request.auth != null && 
                  (resource.data.requestorId == request.auth.uid || 
                   resource.data.providerId == request.auth.uid);
      allow create: if request.auth != null;
      allow update, delete: if request.auth != null && 
                            (resource.data.requestorId == request.auth.uid || 
                             resource.data.providerId == request.auth.uid);
    }
    
    // MESA Track ID mapping data (mostly public)
    match /mesa_tracks/{document=**} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}""",

    "firestore.indexes.json": """{
  "indexes": [
    {
      "collectionGroup": "rights",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "ownerId", "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "rights",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "rightsType", "order": "ASCENDING" },
        { "fieldPath": "workTitle", "order": "ASCENDING" }
      ]
    },
    {
      "collectionGroup": "verifications",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "requestorId", "order": "ASCENDING" },
        { "fieldPath": "status", "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "verifications",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "providerId", "order": "ASCENDING" },
        { "fieldPath": "status", "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    }
  ],
  "fieldOverrides": []
}""",

    "storage.rules": """rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Contract documents - accessible only to owner
    match /contracts/{userId}/{rightId}/{document} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Public verification proofs - readable by anyone, writable by owner
    match /proofs/{rightId}/{proofId} {
      allow read: if true;
      allow write: if request.auth != null && 
                   exists(/databases/$(database)/documents/rights/$(rightId)) &&
                   get(/databases/$(database)/documents/rights/$(rightId)).data.ownerId == request.auth.uid;
    }
    
    // Encrypted verification data - specific permissions
    match /encrypted/{rightId}/{document} {
      allow read: if request.auth != null && 
                 (exists(/databases/$(database)/documents/permissions/$(rightId)/users/$(request.auth.uid)) ||
                  get(/databases/$(database)/documents/rights/$(rightId)).data.ownerId == request.auth.uid);
      allow write: if request.auth != null && 
                   get(/databases/$(database)/documents/rights/$(rightId)).data.ownerId == request.auth.uid;
    }
    
    // User profile images
    match /profiles/{userId} {
      allow read: if true;
      allow write: if request.auth != null && request.auth.uid == userId;
    }
  }
}""",

    "functions/tsconfig.json": """{
  "compilerOptions": {
    "module": "commonjs",
    "noImplicitReturns": true,
    "noUnusedLocals": true,
    "outDir": "lib",
    "sourceMap": true,
    "strict": true,
    "target": "es2017",
    "skipLibCheck": true
  },
  "compileOnSave": true,
  "include": [
    "src"
  ]
}""",

    "functions/package.json": """{
  "name": "mesa-rights-vault-functions",
  "scripts": {
    "build": "tsc",
    "serve": "npm run build && firebase emulators:start --only functions",
    "shell": "npm run build && firebase functions:shell",
    "start": "npm run shell",
    "deploy": "firebase deploy --only functions",
    "logs": "firebase functions:log"
  },
  "engines": {
    "node": "18"
  },
  "main": "lib/index.js",
  "dependencies": {
    "firebase-admin": "^11.9.0",
    "firebase-functions": "^4.4.0",
    "axios": "^1.4.0",
    "crypto-js": "^4.1.1",
    "ethers": "^6.6.2",
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "@google-cloud/vertexai": "^0.1.3"
  },
  "devDependencies": {
    "typescript": "^5.1.6",
    "@typescript-eslint/eslint-plugin": "^5.12.0",
    "@typescript-eslint/parser": "^5.12.0",
    "eslint": "^8.9.0",
    "eslint-config-google": "^0.14.0",
    "eslint-plugin-import": "^2.25.4"
  },
  "private": true
}""",

    "functions/src/index.ts": """import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';
import * as express from 'express';
import * as cors from 'cors';
import axios from 'axios';
import { ethers } from 'ethers';
import { VertexAI } from '@google-cloud/vertexai';

// Initialize Firebase
admin.initializeApp();
const db = admin.firestore();
const storage = admin.storage();

// Initialize Vertex AI
const vertex = new VertexAI({
  project: process.env.GCLOUD_PROJECT || 'mesa-rights-vault',
  location: 'us-central1',
});
const generativeModel = vertex.preview.getGenerativeModel({
  model: 'gemini-pro',
});

// API setup
const app = express();
app.use(cors({ origin: true }));

// Contract Analysis API Endpoint
app.post('/analyze-contract', async (req, res) => {
  try {
    const { contractUrl, userId } = req.body;
    if (!contractUrl || !userId) {
      return res.status(400).json({ error: 'Missing required parameters' });
    }

    // Download contract from Storage
    const bucket = storage.bucket();
    const contractFile = bucket.file(contractUrl);
    const [contractBuffer] = await contractFile.download();
    const contractText = contractBuffer.toString('utf-8');

    // Use Vertex AI to analyze the contract
    const prompt = `
      Analyze the following music rights contract and extract:
      1. Artist/Publisher parties
      2. Rights types (Publishing, Performance, etc.)
      3. Territory information
      4. Term duration
      5. Royalty percentages
      6. Effective date
      
      Format as JSON.
      
      Contract: ${contractText}
    `;

    const result = await generativeModel.generateContent(prompt);
    const response = result.response;
    const contractData = JSON.parse(response.text());
    
    // Store the results in Firestore
    await db.collection('rights').add({
      ownerId: userId,
      contractData: contractData,
      analysisSource: 'vertexai',
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      updatedAt: admin.firestore.FieldValue.serverTimestamp()
    });

    return res.status(200).json({ success: true, data: contractData });
  } catch (error) {
    console.error('Error analyzing contract:', error);
    return res.status(500).json({ error: 'Failed to analyze contract' });
  }
});

// MESA Track ID Integration Endpoint
app.get('/api/track-lookup', async (req, res) => {
    const { title } = req.query;
    if (!title) {
        return res.status(400).json({ error: 'Title parameter is required' });
    }

    try {
        const response = await axios.get(
            `${process.env.MESA_API_BASE}/tracks/search?query=${encodeURIComponent(title)}`,
            {
                headers: {
                    'Authorization': `Bearer ${process.env.MESA_API_KEY}`
                }
            }
        );
        res.json(response.data);
    } catch (error) {
        console.error('MESA API error:', error);
        return res.status(500).json({ error: 'Failed to fetch from MESA Track ID system' });
    }
});

// Zero Knowledge Proof Generation
app.post('/generate-proof', async (req, res) => {
  try {
    const { rightId, claimType, userId } = req.body;
    
    // Get the right document
    const rightDoc = await db.collection('rights').doc(rightId).get();
    if (!rightDoc.exists) {
      return res.status(404).json({ error: 'Right not found' });
    }
    
    const rightData = rightDoc.data();
    if (rightData?.ownerId !== userId) {
      return res.status(403).json({ error: 'Not authorized to generate proof for this right' });
    }
    
    // Generate proof (simplified simulation here)
    const proofData = {
      rightId: rightId,
      claimType: claimType,
      timestamp: Date.now(),
      salt: ethers.utils.randomBytes(16).toString('hex'),
    };
    
    // Create hash of proof data
    const proofHash = ethers.utils.keccak256(
      ethers.utils.toUtf8Bytes(JSON.stringify(proofData))
    );
    
    // Store the proof
    await db.collection('proofs').add({
      rightId: rightId,
      ownerId: userId,
      proofHash: proofHash,
      claimType: claimType,
      timestamp: admin.firestore.FieldValue.serverTimestamp()
    });
    
    return res.status(200).json({ 
      success: true, 
      proofHash: proofHash,
      publicProof: {
        rightId: rightId,
        claimType: claimType,
        proofHash: proofHash
      }
    });
  } catch (error) {
    console.error('Error generating proof:', error);
    return res.status(500).json({ error: 'Failed to generate proof' });
  }
});

// Register the Express app as a function
export const api = functions.https.onRequest(app);

// Firestore triggers
export const onRightCreation = functions.firestore
  .document('rights/{rightId}')
  .onCreate(async (snapshot, context) => {
    const rightData = snapshot.data();
    const rightId = context.params.rightId;
    
    // Create metadata document with public information
    await db.collection('rights').doc(rightId).collection('metadata').doc('public').set({
      workTitle: rightData.contractData?.workTitle || 'Untitled Work',
      rightsType: rightData.contractData?.rightsType || [],
      territory: rightData.contractData?.territory || 'Unknown',
      createdAt: admin.firestore.FieldValue.serverTimestamp()
    });
    
    // Log the creation event
    await db.collection('activityLogs').add({
      action: 'right_created',
      rightId: rightId,
      userId: rightData.ownerId,
      timestamp: admin.firestore.FieldValue.serverTimestamp()
    });
    
    return null;
  });

// When a verification request is created
export const onVerificationRequest = functions.firestore
  .document('verifications/{verificationId}')
  .onCreate(async (snapshot, context) => {
    const verificationData = snapshot.data();
    const verificationId = context.params.verificationId;
    
    // Notify the provider of the verification request
    await db.collection('notifications').add({
      userId: verificationData.providerId,
      type: 'verification_request',
      verificationId: verificationId,
      requestorId: verificationData.requestorId,
      rightId: verificationData.rightId,
      status: 'unread',
      createdAt: admin.firestore.FieldValue.serverTimestamp()
    });
    
    return null;
  });""",

    "remoteconfig.template.json": """{
  "parameters": {
    "feature_selective_disclosure": {
      "defaultValue": {
        "value": "true"
      },
      "description": "Enable/disable selective disclosure of rights data"
    },
    "feature_musicbrainz_integration": {
      "defaultValue": {
        "value": "true"
      },
      "description": "Enable/disable MusicBrainz integration"
    },
    "feature_zk_proofs": {
      "defaultValue": {
        "value": "true"
      },
      "description": "Enable/disable zero-knowledge proofs"
    },
    "feature_mesa_track_id_integration": {
      "defaultValue": {
        "value": "true"
      },
      "description": "Enable/disable MESA Track ID integration"
    },
    "blockchain_network": {
      "defaultValue": {
        "value": "sepolia"
      },
      "description": "Which blockchain network to use (sepolia, mainnet)"
    },
    "api_rate_limit": {
      "defaultValue": {
        "value": "100"
      },
      "description": "API rate limit per user per day"
    }
  },
  "version": {
    "versionNumber": "1",
    "updateTime": "2025-04-09T12:00:00.000Z",
    "updateUser": {
      "email": "admin@mesarightsvault.com"
    },
    "description": "Initial configuration"
  }
}""",

    ".appcheck.json": """{
  "appCheck": {
    "providers": {
      "recaptchaV3": {
        "siteKey": "YOUR_RECAPTCHA_SITE_KEY"
      },
      "play": {
        "enabled": true
      },
      "appAttest": {
        "enabled": true
      }
    }
  }
}""",

    "public/index.html": """<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>MESA Rights Vault</title>
    <style>
      body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin: 0;
        padding: 0;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        background-color: #f5f5f5;
        color: #333;
      }
      .container {
        text-align: center;
        padding: 40px;
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        max-width: 800px;
      }
      h1 {
        color: #4285F4;
        margin-bottom: 1rem;
      }
      p {
        line-height: 1.6;
        margin-bottom: 1.5rem;
      }
      .button {
        display: inline-block;
        background-color: #4285F4;
        color: white;
        padding: 12px 24px;
        border-radius: 4px;
        text-decoration: none;
        font-weight: bold;
        transition: background-color 0.3s;
      }
      .button:hover {
        background-color: #3367D6;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <h1>MESA Rights Vault</h1>
      <p>Privacy-focused music rights management on the Base blockchain</p>
      <p>This is a placeholder page for the MESA Rights Vault web app.</p>
      <p>The complete web application will be deployed here soon.</p>
      <a href="#" class="button">Launch App</a>
    </div>
    
    <!-- Firebase SDK -->
    <script src="/__/firebase/9.6.1/firebase-app-compat.js"></script>
    <script src="/__/firebase/9.6.1/firebase-auth-compat.js"></script>
    <script src="/__/firebase/9.6.1/firebase-firestore-compat.js"></script>
    <script src="/__/firebase/init.js"></script>
  </body>
</html>""",

    "README.md": """# MESA Rights Vault Firebase Configuration

This directory contains all the necessary Firebase configuration files for the MESA Rights Vault project.

## Directory Structure

```
firebase-config/
├── firebase.json            # Main Firebase configuration file
├── firestore.rules          # Security rules for Firestore
├── firestore.indexes.json   # Firestore indexes for queries
├── storage.rules            # Security rules for Cloud Storage
├── remoteconfig.template.json # Remote config template
├── .appcheck.json           # App Check configuration
├── functions/               # Cloud Functions
│   ├── package.json         # Node.js dependencies
│   ├── tsconfig.json        # TypeScript configuration
│   └── src/
│       └── index.ts         # Cloud Functions source code
└── public/                  # Hosting public files
    └── index.html           # Landing page
```

## Deployment Instructions

1. Install Firebase CLI:
   ```
   npm install -g firebase-tools
   ```

2. Login to Firebase:
   ```
   firebase login
   ```

3. Navigate to this directory:
   ```
   cd firebase-config
   ```

4. Initialize the project with your Firebase project ID:
   ```
   firebase use --add
   ```

5. Deploy to Firebase:
   ```
   firebase deploy
   ```

## Initial Setup Tasks

1. Enable services in Firebase Console:
   - Authentication (enable Email/Password, Google providers)
   - Firestore Database
   - Storage
   - Functions
   - Hosting
   - App Check

2. Set up Vertex AI API in Google Cloud Console

3. Configure environment variables in Firebase Functions:
   ```
   firebase functions:config:set blockchain.network="sepolia" blockchain.contract="0x7338af1E9d6dbc4cc1Efa067C0775Bf222aDb0C3"
   ```

## Integration with MESA Rights Vault

This Firebase infrastructure is designed to complement the existing MESA Rights Vault system, providing cloud storage, authentication, and AI-powered contract analysis.

The zero-knowledge proof system in `zk_proofs.py` will be enhanced with cloud functions to provide better scalability and integration with the Base blockchain.
"""
}

def create_directory_structure():
    """Create the directory structure for Firebase files"""
    print(f"Creating directory structure in {BASE_DIR}")
    
    # Create base directory if it doesn't exist
    if os.path.exists(BASE_DIR):
        print(f"Directory {BASE_DIR} already exists. Clearing its contents...")
        shutil.rmtree(BASE_DIR)
    
    # Create main directories
    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "functions", "src"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "public"), exist_ok=True)
    
    # Create and write files
    for file_path, content in FILE_CONTENTS.items():
        full_path = os.path.join(BASE_DIR, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Use UTF-8 encoding when writing files
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Created file: {file_path}")
    
    print("\nFirebase configuration files created successfully!")
    print(f"All files are located in: {BASE_DIR}")
    print("\nTo deploy these files to Firebase:")
    print("1. Install Firebase CLI: npm install -g firebase-tools")
    print("2. Login: firebase login")
    print(f"3. Navigate to: cd {BASE_DIR}")
    print("4. Initialize your project: firebase use --add")
    print("5. Deploy: firebase deploy")

if __name__ == "__main__":
    create_directory_structure() 