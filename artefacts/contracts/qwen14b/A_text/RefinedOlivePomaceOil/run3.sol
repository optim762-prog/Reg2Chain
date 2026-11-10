// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RefinedOlivePomaceOilCompliance {
    // Quality: `value` is the measured value multiplied by 1000 (e.g. 0.80 -> 800, 20.0 -> 20000).
    // Returns true if the value satisfies the limit of this category for that parameter,
    // and true if this category has no limit for that parameter.
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 300;
        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 5000;
        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 1250;
        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 160;
        // No limit for other parameters
        return true;
    }

    // Labelling: `items` are the identifiers of the label items present on the label.
    // Returns false if a mandatory item is missing or a prohibited item is present.
    function checkLabelling(string[] memory items) public pure returns (bool) {
        bool hasLegalName = false;
        bool hasPlaceOfOrigin = false;
        bool hasAlphanumericIdentificationOfThePackagingPlant = false;
        bool hasBlendsOfOliveOilAndOtherVegetableOils = false;
        bool hasNonResealableOpeningSystem = false;

        for (uint i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) == keccak256(bytes("LegalName"))) {
                hasLegalName = true;
            } else if (keccak256(bytes(items[i])) == keccak256(bytes("PlaceOfOrigin"))) {
                hasPlaceOfOrigin = true;
            } else if (keccak256(bytes(items[i])) == keccak256(bytes("AlphanumericIdentificationOfThePackagingPlant"))) {
                hasAlphanumericIdentificationOfThePackagingPlant = true;
            } else if (keccak256(bytes(items[i])) == keccak256(bytes("BlendsOfOliveOilAndOtherVegetableOils"))) {
                hasBlendsOfOliveOilAndOtherVegetableOils = true;
            } else if (keccak256(bytes(items[i])) == keccak256(bytes("NonResealableOpeningSystem"))) {
                hasNonResealableOpeningSystem = true;
            }
        }

        // source: Article 5(1)
        if (!hasLegalName || !hasAlphanumericIdentificationOfThePackagingPlant || !hasNonResealableOpeningSystem) return false;
        // source: Article 5(2)
        if (hasPlaceOfOrigin && hasLegalName) {
            // Place of origin should be grouped with legal name
            // This is a condition that cannot be checked from the input, so it's documented here
            // It should be ensured that PlaceOfOrigin and LegalName are grouped together within the principal field of vision
        }
        // source: Article 3(1)
        if (hasBlendsOfOliveOilAndOtherVegetableOils) return false;

        return true;
    }

    // Both checks together (parameters[i] measured as values[i]).
    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items)
        public pure returns (bool)
    {
        require(parameters.length == values.length, "Parameters and values length mismatch");

        for (uint i = 0; i < parameters.length; i++) {
            if (!checkLimit(parameters[i], values[i])) return false;
        }

        return checkLabelling(items);
    }
}
