// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RefinedOliveOilCompliance {
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        // Acidity limit
        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 300;

        // PeroxideValueMEqO2Kg limit
        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 5000;

        // K268OrK270 limit
        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 1250;

        // DeltaK limit
        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 160;

        // If no limit is found, return true
        return true;
    }

    function checkLabelling(string[] memory items) public pure returns (bool) {
        // Check if mandatory items are present
        // source: Class hierarchy (⊑ = subClassOf)
        for (uint256 i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) == keccak256(bytes("AlphanumericIdentificationOfThePackagingPlant"))) {
                return true;
            }
        }

        // If mandatory item is missing, return false
        return false;
    }

    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items)
        public pure returns (bool) {
        // Check limits
        for (uint256 i = 0; i < parameters.length; i++) {
            if (!checkLimit(parameters[i], values[i])) {
                return false;
            }
        }

        // Check labelling
        if (!checkLabelling(items)) {
            return false;
        }

        // If all checks pass, return true
        return true;
    }
}
