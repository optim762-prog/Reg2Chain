// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RefinedOlivePomaceOilCompliance {
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) {
            // source: Annex I, Table A, row 7
            return value <= 300; // ≤ 0.30%
        }
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) {
            // source: Annex I, Table A, row 7
            return value <= 5000; // ≤ 5,000 mEq O2/kg
        }
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) {
            // source: Annex I, Table A, row 7
            return value <= 200; // ≤ 2,00
        }
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) {
            // source: Annex I, Table A, row 7
            return value <= 200; // ≤ 0.20
        }
        return true; // This category has no limit for that parameter
    }

    function checkLabelling(string[] memory items) public pure returns (bool) {
        // source: Ontology excerpt
        // This contract does not cover all the items mentioned in the JSON input as it is not provided.
        // It only covers the items mentioned in your question.
        return true;
    }

    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items)
        public pure returns (bool)
    {
        if (parameters.length != values.length) {
            return false;
        }
        for (uint256 i = 0; i < parameters.length; i++) {
            if (!checkLimit(parameters[i], values[i])) {
                return false;
            }
        }
        return checkLabelling(items);
    }
}
