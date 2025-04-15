// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

/**
 * @title ISchemaRegistry Interface
 * @dev Interface for the EAS Schema Registry contract.
 * @notice Functions and structs based on EAS documentation.
 */
interface ISchemaRegistry {
    struct SchemaRecord {
        bytes32 uid;
        address resolver;
        bool revocable;
        string schema;
    }

    /**
     * @notice Registers a new schema.
     * @param schema The schema string.
     * @param resolver The optional resolver contract address.
     * @param revocable Whether attestations using this schema are revocable.
     * @return The UID of the new schema.
     */
    function register(string calldata schema, address resolver, bool revocable) external returns (bytes32);

    /**
     * @notice Returns the schema record for a specific UID.
     * @param uid The UID of the schema.
     * @return The schema record.
     */
    function getSchema(bytes32 uid) external view returns (SchemaRecord memory);
} 