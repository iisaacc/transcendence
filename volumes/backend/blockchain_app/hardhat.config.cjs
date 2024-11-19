require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: {
    version: "0.8.18", // Solidity version, adjust if needed
    settings: {
      optimizer: {
        enabled: true,
        runs: 200, // Optimize for gas efficiency
      },
    },
  },
  hardat: {},
  networks: {
    hardhat: {
      chainId: 1337, // Chain ID for the local Hardhat network
      accounts: {
        mnemonic: "test test test test test test test test test test test junk", // Encryption method
        path: "m/44'/60'/0'/0", // The hardhat parent of all the derived keys
        initialIndex: 0, // The initial index to derive
        count: 1, // nb if of accounts to derive
        passphrase: "", // Passphrase for the wallet
      },
      mining: {
        auto: true, // Automatically mine blocks
        interval: 0, // Blocks mined every only on event
      },
    },
    localhost: {
      url: "http://127.0.0.1:8545", // Local Hardhat network for Web3.js
      chainId: 1337, // Match the chain ID with Hardhat
    },
  },
};
