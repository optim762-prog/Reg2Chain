// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ExtraVirginOliveOilCompliance {
    // Quality: `value` is the measured value multiplied by 1000 (e.g. 0.80 -> 800, 20.0 -> 20000).
    // Returns true if the value satisfies the limit of this category for that parameter,
    // and true if this category has no limit for that parameter.
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        // source: Annex I, Table A, row 1
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 800;
        // source: Annex I, Table A, row 1
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 20000;
        // source: Annex I, Table A, row 1
        if (keccak256(bytes(parameter)) == keccak256(bytes("K232"))) return value <= 2500;
        // source: Annex I, Table A, row 1
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 220;
        // source: Annex I, Table A, row 1
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 10;
        // source: Annex I, Table A, row 1
        if (keccak256(bytes(parameter)) == keccak256(bytes("MedianOfDefectMd"))) return value == 0;
        // source: Annex I, Table A, row 1
        if (keccak256(bytes(parameter)) == keccak256(bytes("FruityMedianMf"))) return value > 0;
        // source: Annex I, Table A, row 1
        if (keccak256(bytes(parameter)) == keccak256(bytes("FattyAcidEthylEstersMgKg"))) return value <= 35000;
        // source: Article 4(1)
        if (keccak256(bytes(parameter)) == keccak256(bytes("PackagingCapacity"))) return value <= 5000;

        // No limit for other parameters
        return true;
    }

    // Labelling: `items` are the identifiers of the label items present on the label.
    // Returns false if a mandatory item is missing or a prohibited item is present.
    function checkLabelling(string[] memory items) public pure returns (bool) {
        // source: Article 5(1)
        if (!contains(items, "MandatoryLabellingParticulars")) return false;
        // source: Article 7
        if (!contains(items, "InformationOnTheSpecialStorageConditions")) return false;
        // source: Article 8(1)
        if (!contains(items, "PlaceOfOrigin")) return false;
        // source: Article 9
        if (!contains(items, "AlphanumericIdentificationOfThePackagingPlant")) return false;
        // source: Article 4(1)
        if (!contains(items, "NonResealableOpeningSystem")) return false;
        // source: Article 6(1), read with Article 5(1)
        if (!contains(items, "LegalName")) return false;
        // source: Article 6(2)(a)
        if (!contains(items, "SuperiorCategoryOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans")) return false;

        // No prohibited items specified
        return true;
    }

    // Both checks together (parameters[i] measured as values[i]).
    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items)
        public pure returns (bool)
    {
        require(parameters.length == values.length, "Parameters and values length mismatch");

        for (uint256 i = 0; i < parameters.length; i++) {
            if (!checkLimit(parameters[i], values[i])) return false;
        }

        return checkLabelling(items);
    }

    // Helper function to check if an array contains a specific string
    function contains(string[] memory array, string memory value) internal pure returns (bool) {
        for (uint256 i = 0; i < array.length; i++) {
            if (keccak256(bytes(array[i])) == keccak256(bytes(value))) return true;
        }
        return false;
    }
}
