#!/usr/bin/env python3
"""
Firebase Configuration Generator for MESA Rights Vault

This script generates the necessary Firebase configuration files for the MESA Rights Vault project,
including authentication settings, database rules, storage rules, and functions configuration.
"""

import os
import json
import argparse
from pathlib import Path

class FirebaseConfigGenerator:
    def __init__(self, output_dir="firebase_config"):
        self.output_dir = output_dir
        self.base_dir = Path(output_dir)
        
    def create_directory_structure(self):
        """Create the necessary directory structure for Firebase configuration"""
        directories = [
            self.base_dir,
            self.base_dir / "functions",
            self.base_dir / "database",
            self.base_dir / "storage",
            self.base_dir / "auth"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
    
    def generate_firebase_json(self):
        """Generate the main firebase.json configuration file"""
        config = {
            "database": {
                "rules": "database/database.rules.json"
            },
            "firestore": {
                "rules": "firestore.rules",
                "indexes": "firestore.indexes.json"
            },
            "functions": {
                "source": "functions"
            },
            "hosting": {
                "public": "public",
                "ignore": [
                    "firebase.json",
                    "**/.*",
                    "**/node_modules/**"
                ],
                "rewrites": [
                    {
                        "source": "**",
                        "destination": "/index.html"
                    }
                ]
            },
            "storage": {
                "rules": "storage/storage.rules"
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
                "database": {
                    "port": 9000
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
            }
        }
        
        with open(self.base_dir / "firebase.json", "w") as f:
            json.dump(config, f, indent=2)
            print(f"Created firebase.json")
    
    def generate_database_rules(self):
        """Generate database rules configuration"""
        rules = {
            "rules": {
                "rights": {
                    ".read": "auth != null",
                    ".write": "auth != null && auth.token.admin === true",
                    "$rightId": {
                        ".read": "auth != null && (auth.uid === data.child('ownerId').val() || auth.token.admin === true)",
                        ".write": "auth != null && (auth.uid === data.child('ownerId').val() || auth.token.admin === true)"
                    }
                },
                "users": {
                    "$uid": {
                        ".read": "auth != null && auth.uid === $uid",
                        ".write": "auth != null && auth.uid === $uid"
                    }
                },
                "transactions": {
                    ".read": "auth != null && auth.token.admin === true",
                    ".write": "auth != null",
                    "$transactionId": {
                        ".read": "auth != null && (auth.uid === data.child('participantId').val() || auth.token.admin === true)"
                    }
                }
            }
        }
        
        with open(self.base_dir / "database" / "database.rules.json", "w") as f:
            json.dump(rules, f, indent=2)
            print(f"Created database rules")
    
    def generate_storage_rules(self):
        """Generate storage rules configuration"""
        rules = """rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Default deny
    match /{allPaths=**} {
      allow read, write: if false;
    }
    
    // Rights proofs can be read by the document owner
    match /rights/{rightId}/{proofId} {
      allow read: if request.auth != null && 
                   (request.auth.uid == resource.metadata.ownerId || 
                    request.auth.token.admin == true);
      allow write: if request.auth != null && 
                    (request.auth.uid == request.resource.metadata.ownerId || 
                     request.auth.token.admin == true);
    }
    
    // Encrypted metadata can be read by the owner
    match /metadata/{metadataId} {
      allow read: if request.auth != null && 
                   (request.auth.uid == resource.metadata.ownerId || 
                    request.auth.token.admin == true);
      allow write: if request.auth != null && 
                    (request.auth.uid == request.resource.metadata.ownerId || 
                     request.auth.token.admin == true);
    }
    
    // Public proofs can be read by anyone
    match /public_proofs/{proofId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && request.auth.token.admin == true;
    }
  }
}
"""
        
        with open(self.base_dir / "storage" / "storage.rules", "w") as f:
            f.write(rules)
            print(f"Created storage rules")
    
    def generate_firestore_rules(self):
        """Generate Firestore rules configuration"""
        rules = """rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Default deny all
    match /{document=**} {
      allow read, write: if false;
    }
    
    match /rights/{rightId} {
      allow read: if request.auth != null && 
                   (request.auth.uid == resource.data.ownerId || 
                    get(/databases/$(database)/documents/rights/$(rightId)/access/$(request.auth.uid)).data.hasAccess == true || 
                    request.auth.token.admin == true);
      allow write: if request.auth != null && 
                    (request.auth.uid == resource.data.ownerId || 
                     request.auth.token.admin == true);
                     
      match /access/{userId} {
        allow read: if request.auth != null && 
                     (request.auth.uid == userId || 
                      request.auth.uid == get(/databases/$(database)/documents/rights/$(rightId)).data.ownerId ||
                      request.auth.token.admin == true);
        allow write: if request.auth != null && 
                      (request.auth.uid == get(/databases/$(database)/documents/rights/$(rightId)).data.ownerId || 
                       request.auth.token.admin == true);
      }
      
      match /history/{eventId} {
        allow read: if request.auth != null && 
                     (request.auth.uid == get(/databases/$(database)/documents/rights/$(rightId)).data.ownerId || 
                      get(/databases/$(database)/documents/rights/$(rightId)/access/$(request.auth.uid)).data.hasAccess == true || 
                      request.auth.token.admin == true);
        allow write: if request.auth != null && 
                      (request.auth.uid == get(/databases/$(database)/documents/rights/$(rightId)).data.ownerId || 
                       request.auth.token.admin == true);
      }
    }
    
    match /users/{userId} {
      allow read: if request.auth != null && 
                   (request.auth.uid == userId || 
                    request.auth.token.admin == true);
      allow write: if request.auth != null && 
                    (request.auth.uid == userId || 
                     request.auth.token.admin == true);
                     
      match /rights/{rightId} {
        allow read: if request.auth != null && 
                     (request.auth.uid == userId || 
                      request.auth.token.admin == true);
        allow write: if request.auth != null && 
                      (request.auth.uid == userId || 
                       request.auth.token.admin == true);
      }
    }
  }
}
"""
        
        with open(self.base_dir / "firestore.rules", "w") as f:
            f.write(rules)
            print(f"Created Firestore rules")
    
    def generate_firestore_indexes(self):
        """Generate Firestore indexes configuration"""
        indexes = {
            "indexes": [
                {
                    "collectionGroup": "rights",
                    "queryScope": "COLLECTION",
                    "fields": [
                        {
                            "fieldPath": "ownerId",
                            "order": "ASCENDING"
                        },
                        {
                            "fieldPath": "createdAt",
                            "order": "DESCENDING"
                        }
                    ]
                },
                {
                    "collectionGroup": "rights",
                    "queryScope": "COLLECTION",
                    "fields": [
                        {
                            "fieldPath": "territory",
                            "order": "ASCENDING"
                        },
                        {
                            "fieldPath": "rightsType",
                            "order": "ASCENDING"
                        }
                    ]
                },
                {
                    "collectionGroup": "history",
                    "queryScope": "COLLECTION",
                    "fields": [
                        {
                            "fieldPath": "rightId",
                            "order": "ASCENDING"
                        },
                        {
                            "fieldPath": "timestamp",
                            "order": "DESCENDING"
                        }
                    ]
                }
            ],
            "fieldOverrides": []
        }
        
        with open(self.base_dir / "firestore.indexes.json", "w") as f:
            json.dump(indexes, f, indent=2)
            print(f"Created Firestore indexes")
    
    def generate_auth_config(self):
        """Generate authentication configuration"""
        config = {
            "allowedAuthDomains": ["mesarightsvault.com"],
            "providers": {
                "email": {
                    "enabled": True,
                    "passwordRequirements": {
                        "minLength": 8,
                        "containsLowercase": True,
                        "containsUppercase": True,
                        "containsNumeric": True,
                        "containsNonAlphanumeric": True
                    }
                },
                "google": {
                    "enabled": True
                },
                "phone": {
                    "enabled": True
                }
            },
            "mfa": {
                "enabled": True,
                "enforced": False
            },
            "emailLinkSignIn": {
                "enabled": True,
                "domainAllowlist": ["mesarightsvault.com"]
            }
        }
        
        with open(self.base_dir / "auth" / "auth_config.json", "w") as f:
            json.dump(config, f, indent=2)
            print(f"Created authentication config")
    
    def generate_functions_package(self):
        """Generate functions package.json"""
        package = {
            "name": "mesa-rights-vault-functions",
            "description": "Cloud Functions for MESA Rights Vault",
            "scripts": {
                "lint": "eslint .",
                "serve": "firebase emulators:start --only functions",
                "shell": "firebase functions:shell",
                "start": "npm run shell",
                "deploy": "firebase deploy --only functions",
                "logs": "firebase functions:log"
            },
            "engines": {
                "node": "16"
            },
            "main": "index.js",
            "dependencies": {
                "firebase-admin": "^11.8.0",
                "firebase-functions": "^4.3.1",
                "crypto": "^1.0.1",
                "ethers": "^5.7.2"
            },
            "devDependencies": {
                "eslint": "^8.15.0",
                "eslint-config-google": "^0.14.0"
            },
            "private": true
        }
        
        with open(self.base_dir / "functions" / "package.json", "w") as f:
            json.dump(package, f, indent=2)
            print(f"Created functions package.json")
    
    def generate_function_index(self):
        """Generate functions index.js"""
        index_js = """const functions = require('firebase-functions');
const admin = require('firebase-admin');
const crypto = require('crypto');
const ethers = require('ethers');

admin.initializeApp();

// Create a user profile when new user signs up
exports.createUserProfile = functions.auth.user().onCreate((user) => {
  return admin.firestore().collection('users').doc(user.uid).set({
    email: user.email,
    displayName: user.displayName || '',
    photoURL: user.photoURL || '',
    createdAt: admin.firestore.FieldValue.serverTimestamp(),
    rightsCount: 0,
    isVerified: false
  });
});

// Register a new music right
exports.registerMusicRight = functions.https.onCall(async (data, context) => {
  // Ensure user is authenticated
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'User must be authenticated');
  }
  
  const userId = context.auth.uid;
  
  // Validate the input data
  if (!data.workTitle || !data.artistParty || !data.rightsType) {
    throw new functions.https.HttpsError('invalid-argument', 'Missing required fields');
  }
  
  try {
    // Generate a unique right ID
    const rightId = crypto.randomBytes(16).toString('hex');
    
    // Create the right document
    const rightData = {
      rightId,
      workTitle: data.workTitle,
      artistParty: data.artistParty,
      publisherParty: data.publisherParty || '',
      rightsType: data.rightsType,
      percentage: data.percentage || 100,
      territory: data.territory || 'WORLDWIDE',
      term: data.term || 'PERPETUITY',
      effectiveDate: data.effectiveDate || admin.firestore.FieldValue.serverTimestamp(),
      expirationDate: data.expirationDate || null,
      identifiers: data.identifiers || {},
      ownerId: userId,
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      updatedAt: admin.firestore.FieldValue.serverTimestamp(),
      privacySettings: data.privacySettings || {
        publicFields: ['workTitle', 'rightsType', 'territory'],
        encryptedFields: true
      },
      isActive: true,
      isVerified: false
    };
    
    // Save to Firestore
    await admin.firestore().collection('rights').doc(rightId).set(rightData);
    
    // Update user's rights count
    await admin.firestore().collection('users').doc(userId).update({
      rightsCount: admin.firestore.FieldValue.increment(1)
    });
    
    // Create a history entry
    await admin.firestore().collection('rights').doc(rightId)
      .collection('history').add({
        eventType: 'CREATION',
        timestamp: admin.firestore.FieldValue.serverTimestamp(),
        userId,
        details: 'Right created'
      });
    
    return {
      success: true,
      rightId
    };
  } catch (error) {
    console.error('Error registering music right:', error);
    throw new functions.https.HttpsError('internal', 'Failed to register music right');
  }
});

// Verify a music right against external sources (simulated)
exports.verifyMusicRight = functions.https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'User must be authenticated');
  }
  
  const { rightId } = data;
  if (!rightId) {
    throw new functions.https.HttpsError('invalid-argument', 'Right ID is required');
  }
  
  try {
    // Get the right
    const rightDoc = await admin.firestore().collection('rights').doc(rightId).get();
    if (!rightDoc.exists) {
      throw new functions.https.HttpsError('not-found', 'Right not found');
    }
    
    const rightData = rightDoc.data();
    
    // Ensure the user has access
    if (rightData.ownerId !== context.auth.uid && !context.auth.token.admin) {
      throw new functions.https.HttpsError('permission-denied', 'User does not have permission to verify this right');
    }
    
    // Simulate verification with external database
    // In a real implementation, this would check against MusicBrainz or similar
    const verificationResult = {
      isVerified: true,
      confidence: 0.85,
      matchedFields: ['workTitle', 'artistParty'],
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      verificationSource: 'simulated'
    };
    
    // Update the right with verification status
    await admin.firestore().collection('rights').doc(rightId).update({
      isVerified: true,
      verificationData: verificationResult
    });
    
    // Add to history
    await admin.firestore().collection('rights').doc(rightId)
      .collection('history').add({
        eventType: 'VERIFICATION',
        timestamp: admin.firestore.FieldValue.serverTimestamp(),
        userId: context.auth.uid,
        details: 'Right verified with external source'
      });
    
    return {
      success: true,
      verification: verificationResult
    };
  } catch (error) {
    console.error('Error verifying music right:', error);
    throw new functions.https.HttpsError('internal', 'Failed to verify music right');
  }
});

// Simulates creating a zero-knowledge proof for a right
exports.createZKProof = functions.https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'User must be authenticated');
  }
  
  const { rightId, proofType } = data;
  if (!rightId || !proofType) {
    throw new functions.https.HttpsError('invalid-argument', 'Right ID and proof type are required');
  }
  
  try {
    // Get the right
    const rightDoc = await admin.firestore().collection('rights').doc(rightId).get();
    if (!rightDoc.exists) {
      throw new functions.https.HttpsError('not-found', 'Right not found');
    }
    
    const rightData = rightDoc.data();
    
    // Ensure the user has access
    if (rightData.ownerId !== context.auth.uid && !context.auth.token.admin) {
      throw new functions.https.HttpsError('permission-denied', 'User does not have permission to create proof for this right');
    }
    
    // Simulate ZK proof creation (this would use a real ZK library in production)
    let proofData;
    
    // Create a random wallet to simulate signature
    const wallet = ethers.Wallet.createRandom();
    const message = `${rightId}:${proofType}:${Date.now()}`;
    const signature = await wallet.signMessage(message);
    
    switch (proofType) {
      case 'ownership':
        proofData = {
          rightId,
          proofType,
          ownershipCommitment: crypto.createHash('sha256').update(rightData.ownerId).digest('hex'),
          timestamp: Date.now(),
          signature
        };
        break;
        
      case 'selective_disclosure':
        proofData = {
          rightId,
          proofType,
          disclosedFields: data.disclosedFields || ['workTitle', 'rightsType'],
          publicValues: {
            workTitle: rightData.workTitle,
            rightsType: rightData.rightsType
          },
          timestamp: Date.now(),
          signature
        };
        break;
        
      case 'royalty':
        proofData = {
          rightId,
          proofType,
          royaltyCommitment: crypto.createHash('sha256').update(String(rightData.percentage)).digest('hex'),
          timestamp: Date.now(),
          signature
        };
        break;
        
      default:
        throw new functions.https.HttpsError('invalid-argument', 'Invalid proof type');
    }
    
    // Save the proof
    const proofId = crypto.randomBytes(8).toString('hex');
    await admin.firestore().collection('proofs').doc(proofId).set({
      ...proofData,
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      createdBy: context.auth.uid
    });
    
    // Add reference to the right
    await admin.firestore().collection('rights').doc(rightId)
      .collection('proofs').doc(proofId).set({
        proofId,
        proofType,
        createdAt: admin.firestore.FieldValue.serverTimestamp()
      });
    
    // Add to history
    await admin.firestore().collection('rights').doc(rightId)
      .collection('history').add({
        eventType: 'PROOF_CREATION',
        timestamp: admin.firestore.FieldValue.serverTimestamp(),
        userId: context.auth.uid,
        details: `Created ${proofType} proof`
      });
    
    return {
      success: true,
      proofId,
      proof: proofData
    };
  } catch (error) {
    console.error('Error creating ZK proof:', error);
    throw new functions.https.HttpsError('internal', 'Failed to create ZK proof');
  }
});

// Grant access to a right
exports.grantAccess = functions.https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'User must be authenticated');
  }
  
  const { rightId, targetUserId, accessLevel } = data;
  if (!rightId || !targetUserId || !accessLevel) {
    throw new functions.https.HttpsError('invalid-argument', 'Missing required fields');
  }
  
  try {
    const rightDoc = await admin.firestore().collection('rights').doc(rightId).get();
    if (!rightDoc.exists) {
      throw new functions.https.HttpsError('not-found', 'Right not found');
    }
    
    const rightData = rightDoc.data();
    
    // Ensure the user has ownership
    if (rightData.ownerId !== context.auth.uid && !context.auth.token.admin) {
      throw new functions.https.HttpsError('permission-denied', 'User does not have permission to grant access');
    }
    
    // Validate that the target user exists
    const userDoc = await admin.firestore().collection('users').doc(targetUserId).get();
    if (!userDoc.exists) {
      throw new functions.https.HttpsError('not-found', 'Target user not found');
    }
    
    // Set the access
    await admin.firestore().collection('rights').doc(rightId)
      .collection('access').doc(targetUserId).set({
        userId: targetUserId,
        accessLevel,
        hasAccess: true,
        grantedBy: context.auth.uid,
        grantedAt: admin.firestore.FieldValue.serverTimestamp()
      });
    
    // Add to history
    await admin.firestore().collection('rights').doc(rightId)
      .collection('history').add({
        eventType: 'ACCESS_GRANTED',
        timestamp: admin.firestore.FieldValue.serverTimestamp(),
        userId: context.auth.uid,
        targetUserId,
        details: `Access granted to user with level: ${accessLevel}`
      });
    
    return {
      success: true
    };
  } catch (error) {
    console.error('Error granting access:', error);
    throw new functions.https.HttpsError('internal', 'Failed to grant access');
  }
});

// Revoke access to a right
exports.revokeAccess = functions.https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'User must be authenticated');
  }
  
  const { rightId, targetUserId } = data;
  if (!rightId || !targetUserId) {
    throw new functions.https.HttpsError('invalid-argument', 'Missing required fields');
  }
  
  try {
    const rightDoc = await admin.firestore().collection('rights').doc(rightId).get();
    if (!rightDoc.exists) {
      throw new functions.https.HttpsError('not-found', 'Right not found');
    }
    
    const rightData = rightDoc.data();
    
    // Ensure the user has ownership
    if (rightData.ownerId !== context.auth.uid && !context.auth.token.admin) {
      throw new functions.https.HttpsError('permission-denied', 'User does not have permission to revoke access');
    }
    
    // Revoke access
    await admin.firestore().collection('rights').doc(rightId)
      .collection('access').doc(targetUserId).update({
        hasAccess: false,
        revokedBy: context.auth.uid,
        revokedAt: admin.firestore.FieldValue.serverTimestamp()
      });
    
    // Add to history
    await admin.firestore().collection('rights').doc(rightId)
      .collection('history').add({
        eventType: 'ACCESS_REVOKED',
        timestamp: admin.firestore.FieldValue.serverTimestamp(),
        userId: context.auth.uid,
        targetUserId,
        details: 'Access revoked'
      });
    
    return {
      success: true
    };
  } catch (error) {
    console.error('Error revoking access:', error);
    throw new functions.https.HttpsError('internal', 'Failed to revoke access');
  }
});
"""
        
        with open(self.base_dir / "functions" / "index.js", "w") as f:
            f.write(index_js)
            print(f"Created functions index.js")
    
    def generate_all(self):
        """Generate all Firebase configuration files"""
        self.create_directory_structure()
        self.generate_firebase_json()
        self.generate_database_rules()
        self.generate_storage_rules()
        self.generate_firestore_rules()
        self.generate_firestore_indexes()
        self.generate_auth_config()
        self.generate_functions_package()
        self.generate_function_index()
        print("All Firebase configuration files generated successfully!")

def main():
    parser = argparse.ArgumentParser(description="Generate Firebase configuration for MESA Rights Vault")
    parser.add_argument("--output", default="firebase_config", help="Output directory for Firebase configuration")
    args = parser.parse_args()
    
    generator = FirebaseConfigGenerator(output_dir=args.output)
    generator.generate_all()
    
    print(f"Firebase configuration files generated in '{args.output}' directory")

if __name__ == "__main__":
    main() 