#! /bin/sh -l

# Install hardhat dependencies
echo "Installing npm"
npm install -g npm@10.9.0
echo "Installing hardhat dependencies"
npm install --save-dev hardhat --no-audit
echo "Installing hardhat plugins"
npm install --save-dev @nomicfoundation/hardhat-toolbox --no-audit
#npm install ethers@latest

# Start the hardhat node in the background
npx hardhat node &

# Wait for the node to be ready
sleep 10

# Compile and deploy the contract
npx hardhat compile
sleep 2
npx hardhat run scripts/deploy.js --network localhost

# Keep the script running to maintain the node
wait