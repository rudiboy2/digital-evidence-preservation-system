const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with account:", deployer.address);

  const EvidenceRegistry = await ethers.getContractFactory("EvidenceRegistry");
  const registry = await EvidenceRegistry.deploy(deployer.address);
  await registry.waitForDeployment();
  const registryAddress = await registry.getAddress();
  console.log("EvidenceRegistry deployed to:", registryAddress);

  const CustodyContract = await ethers.getContractFactory("CustodyContract");
  const custody = await CustodyContract.deploy(deployer.address);
  await custody.waitForDeployment();
  const custodyAddress = await custody.getAddress();
  console.log("CustodyContract deployed to:", custodyAddress);

  console.log("\n=== Update your .env file ===");
  console.log("EVIDENCE_REGISTRY_CONTRACT_ADDRESS=" + registryAddress);
  console.log("CUSTODY_CONTRACT_ADDRESS=" + custodyAddress);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
