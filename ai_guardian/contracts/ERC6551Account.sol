// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

/**
 * @title IERC6551Account
 * @dev Interface for ERC-6551 token bound accounts
 */
interface IERC6551Account {
    receive() external payable;
    function token() external view returns (uint256 chainId, address tokenContract, uint256 tokenId);
    function isValidSigner(address signer, bytes calldata) external view returns (bytes4);
}

/**
 * @title ERC6551Account
 * @dev Base implementation of ERC-6551 token bound account
 */
abstract contract ERC6551Account is IERC6551Account {
    // Each account is associated with a single NFT
    uint256 private _chainId;
    address private _tokenContract;
    uint256 private _tokenId;
    
    /**
     * @dev Returns information about the NFT that owns this account
     * @return chainId The chainId where the NFT exists
     * @return tokenContract The address of the NFT contract
     * @return tokenId The ID of the NFT
     */
    function token() external view returns (uint256 chainId, address tokenContract, uint256 tokenId) {
        return (_chainId, _tokenContract, _tokenId);
    }

    /**
     * @dev Initializes the account with token information
     * This is automatically called during account creation
     */
    function _initialize(uint256 chainId_, address tokenContract_, uint256 tokenId_) internal {
        if (_tokenContract != address(0)) revert("Account already initialized");
        
        _chainId = chainId_;
        _tokenContract = tokenContract_;
        _tokenId = tokenId_;
    }
    
    /**
     * @dev Returns information about the NFT that owns this account (internal version)
     */
    function _token() internal view returns (uint256 chainId, address tokenContract, uint256 tokenId) {
        return (_chainId, _tokenContract, _tokenId);
    }
    
    /**
     * @dev Default receive function that allows the account to receive native tokens
     */
    receive() external payable virtual {}
    
    /**
     * @dev Allows the account to accept ERC-1155 token transfers
     */
    function onERC1155Received(
        address,
        address,
        uint256,
        uint256,
        bytes calldata
    ) external pure returns (bytes4) {
        return bytes4(keccak256("onERC1155Received(address,address,uint256,uint256,bytes)"));
    }
    
    /**
     * @dev Allows the account to accept ERC-1155 batch transfers
     */
    function onERC1155BatchReceived(
        address,
        address,
        uint256[] calldata,
        uint256[] calldata,
        bytes calldata
    ) external pure returns (bytes4) {
        return bytes4(keccak256("onERC1155BatchReceived(address,address,uint256[],uint256[],bytes)"));
    }
    
    /**
     * @dev Allows the account to receive ERC-721 tokens
     */
    function onERC721Received(
        address,
        address,
        uint256,
        bytes calldata
    ) external pure returns (bytes4) {
        return bytes4(keccak256("onERC721Received(address,address,uint256,bytes)"));
    }
    
    /**
     * @dev Interface support check
     */
    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == type(IERC6551Account).interfaceId;
    }
} 