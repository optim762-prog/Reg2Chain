// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VirginOliveOilCompliance {
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 2000;
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 20000;
        if (keccak256(bytes(parameter)) == keccak256(bytes("K232"))) return value <= 2600;
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 250;
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 100;
        if (keccak256(bytes(parameter)) == keccak256(bytes("MedianOfDefectMd"))) return value <= 3500;
        if (keccak256(bytes(parameter)) == keccak256(bytes("FruityMedianMf"))) return value > 0;
        if (keccak256(bytes(parameter)) == keccak256(bytes("PackagingCapacity"))) return value <= 5000;
        return true; // No limit for this parameter
    }

    function checkLabelling(string[] memory items) public pure returns (bool) {
        bool hasMandatoryLabellingParticulars = false;
        bool hasInformationOnTheSpecialStorageConditions = false;
        bool hasAlphanumericIdentificationOfThePackagingPlant = false;
        bool hasNonResealableOpeningSystem = false;
        bool hasLegalName = false;
        bool hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = false;

        for (uint i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) == keccak256(bytes("MandatoryLabellingParticulars"))) hasMandatoryLabellingParticulars = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("InformationOnTheSpecialStorageConditions"))) hasInformationOnTheSpecialStorageConditions = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("AlphanumericIdentificationOfThePackagingPlant"))) hasAlphanumericIdentificationOfThePackagingPlant = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("NonResealableOpeningSystem"))) hasNonResealableOpeningSystem = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("LegalName"))) hasLegalName = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("OliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans"))) hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = true;
        }

        return hasMandatoryLabellingParticulars && hasInformationOnTheSpecialStorageConditions && hasAlphanumericIdentificationOfThePackagingPlant && hasNonResealableOpeningSystem && hasLegalName && hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans;
    }

    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items) public pure returns (bool) {
        require(parameters.length == values.length, "Parameters and values arrays must have the same length");

        for (uint i = 0; i < parameters.length; i++) {
            if (!checkLimit(parameters[i], values[i])) return false;
        }

        return checkLabelling(items);
    }
}
