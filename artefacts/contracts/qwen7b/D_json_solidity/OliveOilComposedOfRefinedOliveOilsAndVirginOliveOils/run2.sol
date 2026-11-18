// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract OliveOilComposedOfRefinedOliveOilsAndVirginOliveOilsCompliance {
    // Quality limits
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 1000; // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 15000; // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 1150; // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 150; // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("PackagingCapacity"))) return value <= 5000; // source: Article 4(1)
        return true;
    }

    // Labelling obligations
    function checkLabelling(string[] memory items) public pure returns (bool) {
        bool hasMandatoryLabellingParticulars = false;
        bool hasInformationOnTheSpecialStorageConditions = false;
        bool hasAlphanumericIdentificationOfThePackagingPlant = false;
        bool hasNonResealableOpeningSystem = false;
        bool hasLegalName = false;
        bool hasOilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives = false;

        for (uint i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) == keccak256(bytes("MandatoryLabellingParticulars"))) hasMandatoryLabellingParticulars = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("InformationOnTheSpecialStorageConditions"))) hasInformationOnTheSpecialStorageConditions = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("AlphanumericIdentificationOfThePackagingPlant"))) hasAlphanumericIdentificationOfThePackagingPlant = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("NonResealableOpeningSystem"))) hasNonResealableOpeningSystem = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("LegalName"))) hasLegalName = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("OilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives"))) hasOilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives = true;
        }

        return hasMandatoryLabellingParticulars && hasInformationOnTheSpecialStorageConditions && hasAlphanumericIdentificationOfThePackagingPlant && hasNonResealableOpeningSystem && hasLegalName && hasOilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives;
    }

    // Combined check
    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items) public pure returns (bool) {
        if (!checkLimit(parameters[0], values[0])) return false;
        if (!checkLimit(parameters[1], values[1])) return false;
        if (!checkLimit(parameters[2], values[2])) return false;
        if (!checkLimit(parameters[3], values[3])) return false;
        if (!checkLimit(parameters[4], values[4])) return false;
        return checkLabelling(items);
    }
}
