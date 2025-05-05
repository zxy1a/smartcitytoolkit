def recommend_solution(input_data: dict) -> dict:
    tech_req = input_data.get("technical_requirements", {})
    tps = tech_req.get("tps", 1000)
    latency = tech_req.get("latency", 1)
    security = tech_req.get("security_level", "medium").lower()
    city = input_data.get("city_size", "medium").lower()
    budget = input_data.get("budget_range", [0, 100000])
    app = input_data.get("application_scenarios", "").lower()
    tech_stack = [t.lower() for t in input_data.get("technology_stack", [])]

    recommendation = {}

    # BC type
    if "multi-party" in app or "cross-organization" in app or security == "high":
        blockchain_type = "Consortium"
    elif budget[1] > 500000 and city == "large":
        blockchain_type = "Public"
    else:
        blockchain_type = "Private"
    recommendation["blockchain_type"] = blockchain_type

    # platform
    if blockchain_type == "Consortium":
        if security == "high" or "compliance" in app:
            platform = "Hyperledger Fabric"
        else:
            platform = "Quorum"
    elif blockchain_type == "Public":
        if tps > 5000:
            platform = "Solana" if latency < 1 else "Polygon"
        else:
            platform = "Ethereum"
    else:  # Private
        platform = "Hyperledger Besu" if "java" in tech_stack else "Custom Private Chain"
    recommendation["platform"] = platform

    # consensus
    if platform == "Hyperledger Fabric":
        consensus = "PBFT"
    elif platform == "Quorum":
        consensus = "RAFT" if security == "medium" else "IBFT2"
    elif platform in ["Solana", "Polygon", "Ethereum"]:
        consensus = "PoS"
    else:
        consensus = "RAFT"
    recommendation["consensus"] = consensus

    # storage
    if "big data" in app or tps > 2000:
        storage = "Off-chain with IPFS or hybrid"
    elif "audit" in app or "documents" in app or "compliance" in app:
        storage = "On-chain with Merkle proofs"
    else:
        storage = "Off-chain or centralized DB"
    recommendation["storage"] = storage

    # network
    if blockchain_type == "Consortium":
        network = "4–10 nodes across organizations with endorsement policies"
    elif blockchain_type == "Public":
        network = "Participate in validator set or use Layer 2 for performance"
    else:
        network = "1–3 trusted nodes with simplified consensus"
    recommendation["network_suggestion"] = network

    # security
    security_advice = []
    if security == "high":
        security_advice.append("Enable Identity Management (CA / MSP)")
        if blockchain_type != "Public":
            security_advice.append("Use Confidential Transactions or ZKP modules")
    if "voting" in app or "finance" in app:
        security_advice.append("Enable audit log & multi-sig controls")
    recommendation["security_advice"] = security_advice

    return recommendation
