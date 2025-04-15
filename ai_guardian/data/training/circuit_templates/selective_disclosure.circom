pragma circom 2.0.0;

include "node_modules/circomlib/circuits/poseidon.circom";
include "node_modules/circomlib/circuits/comparators.circom";

// Circuit for selectively disclosing specific fields from rights data
template SelectiveDisclosure() {
    // Public inputs - visible on chain
    signal input originalDataHash;   // Hash of the complete original data
    signal input disclosedFieldsHash; // Hash of the disclosed fields
    
    // Private inputs - not revealed
    signal input originalData;       // Original complete data (private)
    signal input disclosedFields;    // Disclosed fields (private)
    signal input undisclosedFields;  // Undisclosed fields (private)
    signal input salt;               // Random salt for privacy
    
    // Verify disclosed + undisclosed = original
    // This is a simplified representation. In a real implementation,
    // we would need to use a more complex check to verify that the merging
    // of disclosed and undisclosed fields equals the original data
    signal combinedFields;
    combinedFields <== disclosedFields + undisclosedFields;
    
    // Check that combinedFields = originalData
    component fieldsCheck = IsEqual();
    fieldsCheck.in[0] <== combinedFields;
    fieldsCheck.in[1] <== originalData;
    
    // Compute hashes
    component originalHasher = Poseidon(2);
    originalHasher.inputs[0] <== originalData;
    originalHasher.inputs[1] <== salt;
    
    component disclosedHasher = Poseidon(2);
    disclosedHasher.inputs[0] <== disclosedFields;
    disclosedHasher.inputs[1] <== salt;
    
    // Check that calculated hashes match the public inputs
    originalHasher.out === originalDataHash;
    disclosedHasher.out === disclosedFieldsHash;
    
    // Additional constraint to ensure fields check passed
    fieldsCheck.out === 1;
}

component main {public [originalDataHash, disclosedFieldsHash]} = SelectiveDisclosure(); 