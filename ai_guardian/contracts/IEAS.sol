// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

/**
 * @title IEAS Interface
 * @dev Interface for the core EAS contract.
 * @notice Functions and structs based on EAS documentation.
 */
interface IEAS {
    struct AttestationRequest {
        bytes32 schema;
        AttestationRequestData data;
    }

    struct AttestationRequestData {
        address recipient;
        uint64 expirationTime; // Use 0 for no expiration
        bool revocable;
        bytes32 refUID; // UID of attestation being referred to, or bytes32(0)
        bytes data;
        uint256 value; // ETH value sent with the attestation
    }

    struct RevocationRequest {
        bytes32 schema;
        RevocationRequestData data;
    }

    struct RevocationRequestData {
        bytes32 uid; // UID of the attestation to revoke
        uint256 value; // ETH value sent with the revocation
    }

    struct Attestation {
        bytes32 uid;
        bytes32 schema;
        uint64 time;
        uint64 expirationTime;
        uint64 revocationTime;
        bytes32 refUID;
        address recipient;
        address attester;
        bool revocable;
        bytes data;
    }

    /**
     * @notice Returns the version of the contract.
     */
    function version() external view returns (string memory);

    /**
     * @notice Attests to a specific schema.
     * @param request The attestation request.
     * @return The UID of the new attestation.
     */
    function attest(AttestationRequest calldata request) external payable returns (bytes32);

    /**
     * @notice Revokes an attestation.
     * @param request The revocation request.
     */
    function revoke(RevocationRequest calldata request) external payable;

    /**
     * @notice Returns the attestation structure for a specific UID.
     * @param uid The UID of the attestation.
     * @return The attestation structure.
     */
    function getAttestation(bytes32 uid) external view returns (Attestation memory);

    /**
     * @notice Returns whether an attestation exists and is valid (i.e., not revoked and not expired).
     * @param uid The UID of the attestation.
     * @return True if the attestation is valid, false otherwise.
     */
    function isAttestationValid(bytes32 uid) external view returns (bool);
} 