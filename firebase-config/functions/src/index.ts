import * as functions from 'firebase-functions';
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
  });