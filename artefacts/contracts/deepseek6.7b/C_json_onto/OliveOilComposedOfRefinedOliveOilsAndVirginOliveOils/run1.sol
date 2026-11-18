// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract OliveOilComposedOfRefinedOliveOilsAndVirginOliveOilsCompliance {
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 1000; // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 15000; // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 1150; // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 150; // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("PackagingCapacity"))) return value <= 5000; // source: Annex I, Table A, row 5
        return true;
    }

    function checkLabelling(string[] memory items) public pure returns (bool) {
        for (uint256 i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) != keccak256(bytes("MandatoryLabellingParticulars")) &&
                keccak256(bytes(items[i])) != keccak256(bytes("InformationOnTheSpecialStorageConditions")) &&
                keccak256(bytes(items[i])) != keccak256(bytes("AlphanumericIdentificationOfThePackagingPlant")) &&
                keccak256(bytes(items[i])) != keccak256(bytes("NonResealableOpeningSystem")) &&
                keccak256(bytes(items[i])) != keccak256(bytes("OliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans")) &&
                keccak256(bytes(items[i])) != keccak256(bytes("OlivePomaceCategoryInformation")) &&
                keccak256(bytes(items[i])) != keccak256(bytes("OptionalReservedTerms")) &&
                keccak256(bytes(items[i])) != keccak256(bytes("PlaceOfOrigin")) &&
                keccak256(bytes(items[i])) != keccak256(bytes("SuperiorCategoryOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans")) &&
                keccak256(bytes(items[i])) != keccak256(bytes("VoluntaryLabellingParticulars")))
                return false;
        }
        return true;
    }

    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items)
        public pure returns (bool)
    {
        if (parameters.length != values.length) return false;
        for (uint256 i = 0; i < parameters.length; i++) {
            if (!checkLimit(parameters[i], values[i])) return false;
        }
        return checkLabelling(items);
    }
}
