pragma solidity ^0.8.20;

contract RefinedOliveOilCompliance {
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) {
            // source: Annex I, Table A, row 4
            return value <= 300; // ≤ 0.30 %
        }
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) {
            // source: Annex I, Table A, row 4
            return value <= 5000; // ≤ 5,0 mEq O2/kg
        }
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) {
            // source: Annex I, Table A, row 4
            return value <= 1250; // ≤ 1,25 dimensionless
        }
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) {
            // source: Annex I, Table A, row 4
            return value <= 160; // ≤ 0.16 dimensionless
        }
        return true; // No limit for this parameter
    }

    function checkLabelling(string[] memory items) public pure returns (bool) {
        // No obligations, permissions or prohibitions are defined in the input
        return true;
    }

    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items)
        public pure returns (bool) {
        require(parameters.length == values.length, "Parameters and values must have the same length");
        for (uint256 i = 0; i < parameters.length; i++) {
            if (!checkLimit(parameters[i], values[i])) {
                return false;
            }
        }
        return checkLabelling(items);
    }
}
