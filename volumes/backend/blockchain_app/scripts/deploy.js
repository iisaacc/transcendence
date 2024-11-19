const hre = require("hardhat");
const fs = require('fs');
const path = './deployedAddress.json';

async function main() {
  const Contract = await hre.ethers.deployContract("TournamentManager", []);

  await Contract.waitForDeployment();

  const contractAddress = await Contract.getAddress();

  // console.log(`Contract deployed to contractAddress: ${contractAddress}`);
  fs.writeFileSync(path, JSON.stringify({ contractAddress: contractAddress }));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
