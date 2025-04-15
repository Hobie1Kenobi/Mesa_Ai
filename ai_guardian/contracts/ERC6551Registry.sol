// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

/**
 * @title ERC6551Registry
 * @dev Registry for ERC-6551 token bound accounts
 */
contract ERC6551Registry {
    event AccountCreated(
        address account,
        address implementation,
        uint256 chainId,
        address tokenContract,
        uint256 tokenId,
        uint256 salt
    );

    /**
     * @dev Creates a token bound account for a given implementation, NFT, and salt
     * @param implementation The account implementation address
     * @param chainId The chainId of the network
     * @param tokenContract The token contract address
     * @param tokenId The token ID
     * @param salt A unique salt for address derivation
     * @param initData Initialization data for the account
     * @return The address of the created account
     */
    function createAccount(
        address implementation,
        uint256 chainId,
        address tokenContract,
        uint256 tokenId,
        uint256 salt,
        bytes calldata initData
    ) external returns (address) {
        bytes memory code = _creationCode(implementation, chainId, tokenContract, tokenId, salt);
        
        address _account = address(uint160(uint256(keccak256(code))));
        
        if (_account.code.length != 0) return _account;
        
        assembly {
            _account := create(0, add(code, 0x20), mload(code))
        }
        
        if (initData.length > 0) {
            (bool success, ) = _account.call(initData);
            require(success, "Initialization failed");
        }
        
        emit AccountCreated(
            _account,
            implementation,
            chainId,
            tokenContract,
            tokenId,
            salt
        );
        
        return _account;
    }

    /**
     * @dev Returns the account address that would be created for given parameters
     * @param implementation The account implementation address
     * @param chainId The chainId of the network
     * @param tokenContract The token contract address
     * @param tokenId The token ID
     * @param salt A unique salt for address derivation
     * @return The account address
     */
    function account(
        address implementation,
        uint256 chainId,
        address tokenContract,
        uint256 tokenId,
        uint256 salt
    ) external view returns (address) {
        bytes memory code = _creationCode(implementation, chainId, tokenContract, tokenId, salt);
        return address(uint160(uint256(keccak256(code))));
    }

    /**
     * @dev Creates the bytecode for account creation
     */
    function _creationCode(
        address implementation_,
        uint256 chainId_,
        address tokenContract_,
        uint256 tokenId_,
        uint256 salt_
    ) internal pure returns (bytes memory) {
        return abi.encodePacked(
            hex"3d602d80600a3d3981f3363d3d373d3d3d363d73",
            implementation_,
            hex"5af43d82803e903d91602b57fd5bf3",
            abi.encode(salt_, chainId_, tokenContract_, tokenId_)
        );
    }
} 