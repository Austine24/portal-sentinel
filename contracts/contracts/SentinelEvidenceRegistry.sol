// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Sentinel Evidence Registry
/// @notice Records compact, tamper-evident fingerprints of security incidents.
///         It stores only a hash and a risk score, never incident details.
///         A record proves THAT a given evidence package existed at a given time
///         and was recorded by an authorised account. It does not prove the incident was real.
contract SentinelEvidenceRegistry {
    struct Record {
        bytes32 evidenceHash; // SHA-256 of the canonical evidence package (computed off-chain)
        uint8 riskScore;      // 0 to 100
        uint64 recordedAt;    // block timestamp, not chosen by the caller
        address recorder;
    }

    address public owner;
    address public pendingOwner;
    uint256 public totalRecords;

    mapping(bytes32 => Record) private records; // key: incidentId

    event EvidenceRecorded(
        bytes32 indexed incidentId,
        bytes32 indexed evidenceHash,
        uint8 riskScore,
        address indexed recorder,
        uint64 recordedAt
    );
    event OwnershipTransferStarted(address indexed currentOwner, address indexed proposedOwner);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    error NotOwner();
    error NotPendingOwner();
    error ZeroAddress();
    error InvalidIncidentId();
    error EmptyHash();
    error InvalidRiskScore(uint8 riskScore);
    error AlreadyRecorded(bytes32 incidentId);
    error NotFound(bytes32 incidentId);

    constructor() {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    /// @notice Record evidence for an incident. Each incident can be recorded exactly once.
    function record(bytes32 incidentId, bytes32 evidenceHash, uint8 riskScore) external onlyOwner {
        // Checks
        if (incidentId == bytes32(0)) revert InvalidIncidentId();
        if (evidenceHash == bytes32(0)) revert EmptyHash();
        if (riskScore > 100) revert InvalidRiskScore(riskScore);
        if (records[incidentId].recordedAt != 0) revert AlreadyRecorded(incidentId);

        // Effects
        uint64 nowTs = uint64(block.timestamp);
        records[incidentId] = Record({
            evidenceHash: evidenceHash,
            riskScore: riskScore,
            recordedAt: nowTs,
            recorder: msg.sender
        });
        totalRecords += 1;

        emit EvidenceRecorded(incidentId, evidenceHash, riskScore, msg.sender, nowTs);
    }

    /// @notice Read a record. Reverts if the incident was never recorded.
    function get(bytes32 incidentId) external view returns (Record memory) {
        Record memory r = records[incidentId];
        if (r.recordedAt == 0) revert NotFound(incidentId);
        return r;
    }

    /// @notice True only if the incident is recorded AND its stored hash equals `evidenceHash`.
    function verify(bytes32 incidentId, bytes32 evidenceHash) external view returns (bool) {
        Record storage r = records[incidentId];
        return r.recordedAt != 0 && r.evidenceHash == evidenceHash;
    }

    /// @notice Step 1 of a two-step ownership change (prevents handing control to a wrong address).
    function transferOwnership(address proposedOwner) external onlyOwner {
        if (proposedOwner == address(0)) revert ZeroAddress();
        pendingOwner = proposedOwner;
        emit OwnershipTransferStarted(owner, proposedOwner);
    }

    /// @notice Step 2: the proposed owner proves it controls its key by accepting.
    function acceptOwnership() external {
        if (msg.sender != pendingOwner) revert NotPendingOwner();
        address previous = owner;
        owner = msg.sender;
        pendingOwner = address(0);
        emit OwnershipTransferred(previous, msg.sender);
    }
}
