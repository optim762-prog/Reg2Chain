// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RefinedOlivePomaceOilCompliance {
    // Quality: Acidity, DeltaK, FattyAcidEthylEstersMgKg, FruityMedianMf, K232, K268OrK270, MedianOfDefectMd, PackagingCapacity, PeroxideValueMEqO2Kg
    // Labelling: AlphanumericIdentificationOfThePackagingPlant, BlendsOfOliveOilAndOtherVegetableOils, ColdExtraction, FirstColdPressing, Foodstuff, HarvestingYear, IndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell, InformationOnTheSpecialStorageConditions, LegalName, MandatoryLabellingParticulars, NonResealableOpeningSystem, OilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives, OliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans, OlivePomaceCategoryInformation, OptionalReservedTerms, PlaceOfOrigin, SuperiorCategoryOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans, VoluntaryLabellingParticulars

    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value * 1000 <= 300; // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value * 1000 <= 5000; // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value * 1000 <= 2000; // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value * 1000 <= 200; // source: Annex I, Table A, row 7
        return true;
    }

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

    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items) public pure returns (bool) {
        if (!checkLimit(parameters[0], values[0])) return false;
        if (!checkLimit(parameters[1], values[1])) return false;
        if (!checkLimit(parameters[2], values[2])) return false;
        if (!checkLimit(parameters[3], values[3])) return false;
        return checkLabelling(items);
    }
}
