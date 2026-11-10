// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RefinedOlivePomaceOilCompliance {
    // Quality limits
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 300; // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 5000; // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 2000; // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 200; // source: Annex I, Table A, row 7
        return true;
    }

    // Labelling
    function checkLabelling(string[] memory items) public pure returns (bool) {
        bool hasLegalName = false;
        bool hasFoodstuff = false;
        bool hasHarvestingYear = false;
        bool hasPlaceOfOrigin = false;
        bool hasOlivePomaceCategoryInformation = false;

        for (uint i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) == keccak256(bytes("LegalName"))) hasLegalName = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("Foodstuff"))) hasFoodstuff = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("HarvestingYear"))) hasHarvestingYear = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("PlaceOfOrigin"))) hasPlaceOfOrigin = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("OlivePomaceCategoryInformation"))) hasOlivePomaceCategoryInformation = true;
        }

        return hasLegalName && hasFoodstuff && hasHarvestingYear && hasPlaceOfOrigin && hasOlivePomaceCategoryInformation;
    }

    // Compliance
    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items) public pure returns (bool) {
        require(parameters.length == values.length, "Parameters and values length mismatch");

        for (uint i = 0; i < parameters.length; i++) {
            if (!checkLimit(parameters[i], values[i])) return false;
        }

        return checkLabelling(items);
    }
}
