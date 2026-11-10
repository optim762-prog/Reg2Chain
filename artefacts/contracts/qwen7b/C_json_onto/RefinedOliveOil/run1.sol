// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RefinedOliveOilCompliance {
    // Quality limits
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value * 1000 <= 300; // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value * 1000 <= 5000; // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value * 1000 <= 1250; // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value * 1000 <= 160; // source: Annex I, Table A, row 4
        return true;
    }

    // Labelling requirements
    function checkLabelling(string[] memory items) public pure returns (bool) {
        bool hasLegalName = false;
        bool hasFoodstuff = false;
        bool hasHarvestingYear = false;
        bool hasPlaceOfOrigin = false;
        bool hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = false;
        bool hasColdExtraction = false;
        bool hasFirstColdPressing = false;
        bool hasNonResealableOpeningSystem = false;
        bool hasInformationOnTheSpecialStorageConditions = false;
        bool hasIndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell = false;
        bool hasVoluntaryLabellingParticulars = false;

        for (uint i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) == keccak256(bytes("LegalName"))) hasLegalName = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("Foodstuff"))) hasFoodstuff = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("HarvestingYear"))) hasHarvestingYear = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("PlaceOfOrigin"))) hasPlaceOfOrigin = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("OliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans"))) hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("ColdExtraction"))) hasColdExtraction = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("FirstColdPressing"))) hasFirstColdPressing = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("NonResealableOpeningSystem"))) hasNonResealableOpeningSystem = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("InformationOnTheSpecialStorageConditions"))) hasInformationOnTheSpecialStorageConditions = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("IndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell"))) hasIndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("VoluntaryLabellingParticulars"))) hasVoluntaryLabellingParticulars = true;
        }

        return hasLegalName && hasFoodstuff && hasHarvestingYear && hasPlaceOfOrigin && hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans && hasColdExtraction && hasFirstColdPressing && hasNonResealableOpeningSystem && hasInformationOnTheSpecialStorageConditions && hasIndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell && hasVoluntaryLabellingParticulars;
    }

    // Combined check
    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items) public pure returns (bool) {
        if (!checkLimit(parameters[0], values[0])) return false;
        if (!checkLimit(parameters[1], values[1])) return false;
        if (!checkLimit(parameters[2], values[2])) return false;
        if (!checkLimit(parameters[3], values[3])) return false;
        return checkLabelling(items);
    }
}
