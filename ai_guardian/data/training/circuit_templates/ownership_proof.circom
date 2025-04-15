pragma circom 2.0.0;

include "node_modules/circomlib/circuits/poseidon.circom";
include "node_modules/circomlib/circuits/comparators.circom";

// Circuit for proving ownership of music rights without revealing sensitive details
template OwnershipProof() {
    // Public inputs - visible on chain
    signal input workIdHash;      // Hash of the work ID
    signal input rightsTypeHash;  // Hash of the rights type
    signal input ownerAddressHash; // Hash of the owner's address
    
    // Private inputs - not revealed
    signal input workId;          // Actual work ID (private)
    signal input rightsType;      // Actual rights type (private)
    signal input ownerAddress;    // Owner's address (private)
    signal input salt;            // Random salt for privacy
    
    // Compute hashes and verify they match the public inputs
    signal workIdCalcHash;
    signal rightsTypeCalcHash;
    signal ownerAddressCalcHash;
    
    // Use Poseidon hash for efficient ZK proofs
    component workIdHasher = Poseidon(2);
    workIdHasher.inputs[0] <== workId;
    workIdHasher.inputs[1] <== salt;
    workIdCalcHash <== workIdHasher.out;
    
    component rightsTypeHasher = Poseidon(2);
    rightsTypeHasher.inputs[0] <== rightsType;
    rightsTypeHasher.inputs[1] <== salt;
    rightsTypeCalcHash <== rightsTypeHasher.out;
    
    component ownerHasher = Poseidon(2);
    ownerHasher.inputs[0] <== ownerAddress;
    ownerHasher.inputs[1] <== salt;
    ownerAddressCalcHash <== ownerHasher.out;
    
    // Check that calculated hashes match the public inputs
    workIdCalcHash === workIdHash;
    rightsTypeCalcHash === rightsTypeHash;
    ownerAddressCalcHash === ownerAddressHash;
    
    // Additional checks can be added here - for example:
    // - Verify expiration date has not passed
    // - Verify territory restrictions
    // - Check for minimum ownership percentage
}

component main {public [workIdHash, rightsTypeHash, ownerAddressHash]} = OwnershipProof(); 