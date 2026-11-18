// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ExtraVirginOliveOilCompliance {
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value * 1000 <= 800;
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value * 1000 <= 20000;
        if (keccak256(bytes(parameter)) == keccak256(bytes("K232"))) return value * 1000 <= 2500;
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value * 1000 <= 220;
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value * 1000 <= 10;
        if (keccak256(bytes(parameter)) == keccak256(bytes("MedianOfDefectMd"))) return value * 1000 == 0;
        if (keccak256(bytes(parameter)) == keccak256(bytes("FruityMedianMf"))) return value * 1000 > 0;
        if (keccak256(bytes(parameter)) == keccak256(bytes("FattyAcidEthylEstersMgKg"))) return value * 1000 <= 35000;
        if (keccak256(bytes(parameter)) == keccak256(bytes("PackagingCapacity"))) return value * 1000 <= 5000;
        return true;
    }

    function checkLabelling(string[] memory items) public pure returns (bool) {
        bool hasLegalName = false;
        bool hasPlaceOfOrigin = false;
        bool hasInformationOnTheSpecialStorageConditions = false;
        bool hasAlphanumericIdentificationOfThePackagingPlant = false;
        bool hasNonResealableOpeningSystem = false;
        bool hasMandatoryLabellingParticulars = false;
        bool hasSuperiorCategoryOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = false;

        for (uint i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) == keccak256(bytes("LegalName"))) hasLegalName = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("PlaceOfOrigin"))) hasPlaceOfOrigin = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("InformationOnTheSpecialStorageConditions"))) hasInformationOnTheSpecialStorageConditions = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("AlphanumericIdentificationOfThePackagingPlant"))) hasAlphanumericIdentificationOfThePackagingPlant = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("NonResealableOpeningSystem"))) hasNonResealableOpeningSystem = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("MandatoryLabellingParticulars"))) hasMandatoryLabellingParticulars = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("SuperiorCategoryOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans"))) hasSuperiorCategoryOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = true;
        }

        return hasLegalName && hasPlaceOfOrigin && hasInformationOnTheSpecialStorageConditions && hasAlphanumericIdentificationOfThePackagingPlant && hasNonResealableOpeningSystem && hasMandatoryLabellingParticulars && hasSuperiorCategoryOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans;
    }

    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items) public pure returns (bool) {
        require(parameters.length == values.length, "Parameters and values length mismatch");

        for (uint i = 0; i < parameters.length; i++) {
            if (!checkLimit(parameters[i], values[i])) return false;
        }

        return checkLabelling(items);
    }
}
