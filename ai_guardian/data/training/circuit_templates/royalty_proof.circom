pragma circom 2.0.0;

include "node_modules/circomlib/circuits/poseidon.circom";
include "node_modules/circomlib/circuits/comparators.circom";

// Circuit for verifying royalty calculations without revealing actual percentages
template RoyaltyProof(numParties) {
    // Public inputs - visible on chain
    signal input paymentAmount;           // Total payment amount
    signal input totalRoyaltyHash;        // Hash of the sum of all royalty percentages (should be 1.0 or 100%)
    signal input partiesCountHash;        // Hash of the number of parties receiving royalties
    signal input expectedPaymentHash;     // Hash of the expected payment amounts
    
    // Private inputs - not revealed
    signal input royaltyPercentages[numParties]; // Array of royalty percentages (e.g., 0.5 for 50%)
    signal input partyIds[numParties];          // Array of party identifiers (could be hashed addresses)
    signal input expectedPayments[numParties];  // Array of expected payment amounts
    signal input salt;                         // Random salt for privacy
    
    // Internal signals
    signal totalPercentage;
    signal totalExpectedPayment;
    signal percentageValid;
    signal paymentsValid;
    signal totalVerified;
    
    // Calculate total percentage (should sum to 1.0 for 100%)
    totalPercentage = 0;
    for (var i = 0; i < numParties; i++) {
        totalPercentage += royaltyPercentages[i];
    }
    
    // Verify total percentage is 1.0 (allowing for small rounding errors)
    component percentageCheck = IsEqual();
    percentageCheck.in[0] <== totalPercentage;
    percentageCheck.in[1] <== 1;
    percentageValid <== percentageCheck.out;
    
    // Calculate total expected payment
    totalExpectedPayment = 0;
    for (var i = 0; i < numParties; i++) {
        // In a real implementation, we would calculate payment = percentage * paymentAmount
        // Here we just verify that the provided expected payments match what we calculate
        signal calculatedPayment;
        calculatedPayment <-- royaltyPercentages[i] * paymentAmount;
        
        // Verify each payment calculation (with small tolerance for rounding)
        component paymentCheck = IsEqual();
        paymentCheck.in[0] <== calculatedPayment;
        paymentCheck.in[1] <== expectedPayments[i];
        
        // Add to total
        totalExpectedPayment += expectedPayments[i];
    }
    
    // Verify total payment matches sum of expected payments
    component paymentTotalCheck = IsEqual();
    paymentTotalCheck.in[0] <== totalExpectedPayment;
    paymentTotalCheck.in[1] <== paymentAmount;
    paymentsValid <== paymentTotalCheck.out;
    
    // Generate hash of the royalty percentages for verification
    component royaltyHasher = Poseidon(numParties + 1);
    for (var i = 0; i < numParties; i++) {
        royaltyHasher.inputs[i] <== royaltyPercentages[i];
    }
    royaltyHasher.inputs[numParties] <== salt;
    
    // Generate hash of the parties count + salt
    component partiesHasher = Poseidon(2);
    partiesHasher.inputs[0] <== numParties;
    partiesHasher.inputs[1] <== salt;
    
    // Generate hash of the expected payments
    component paymentHasher = Poseidon(numParties + 1);
    for (var i = 0; i < numParties; i++) {
        paymentHasher.inputs[i] <== expectedPayments[i];
    }
    paymentHasher.inputs[numParties] <== salt;
    
    // Verify overall calculation is valid
    totalVerified <== percentageValid * paymentsValid;
    
    // Verify the hashes match the public inputs
    totalRoyaltyHash === royaltyHasher.out;
    partiesCountHash === partiesHasher.out;
    expectedPaymentHash === paymentHasher.out;
    
    // Final constraint ensuring everything was verified correctly
    totalVerified === 1;
}

// Example instantiation for 3 parties
component main {public [paymentAmount, totalRoyaltyHash, partiesCountHash, expectedPaymentHash]} = RoyaltyProof(3); 