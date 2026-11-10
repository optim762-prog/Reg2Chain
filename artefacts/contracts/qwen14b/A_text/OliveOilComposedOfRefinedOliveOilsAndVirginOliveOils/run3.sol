// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract OliveOilComposedOfRefinedOliveOilsAndVirginOliveOilsCompliance {
    // Quality: `value` is the measured value multiplied by 1000 (e.g. 0.80 -> 800, 20.0 -> 20000).
    // Returns true if the value satisfies the limit of this category for that parameter,
    // and true if this category has no limit for that parameter.
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 1000;
        // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 15000;
        // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 1150;
        // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 150;
        // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("MedianOfDefectMd"))) return value <= 350;
        // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("FruityMedianMf"))) return value > 0;
        // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("FattyAcidEthylEstersMgKg"))) return value <= 35000;
        // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("PackagingCapacity"))) return value <= 5000;
        return true;
    }

    // Labelling: `items` are the identifiers of the label items present on the label.
    // Returns false if a mandatory item is missing or a prohibited item is present.
    function checkLabelling(string[] memory items) public pure returns (bool) {
        bool hasLegalName = false;
        bool hasPlaceOfOrigin = false;
        bool hasAlphanumericIdentificationOfThePackagingPlant = false;
        bool hasBlendsOfOliveOilAndOtherVegetableOils = false;
        bool hasColdExtraction = false;
        bool hasFirstColdPressing = false;
        bool hasFoodstuff = false;
        bool hasHarvestingYear = false;
        bool hasIndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell = false;
        bool hasInformationOnTheSpecialStorageConditions = false;
        bool hasNonResealableOpeningSystem = false;
        bool hasOilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives = false;
        bool hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = false;
        bool hasOlivePomaceCategoryInformation = false;
        bool hasOptionalReservedTerms = false;
        bool hasVoluntaryLabellingParticulars = false;

        for (uint i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) == keccak256(bytes("LegalName"))) hasLegalName = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("PlaceOfOrigin"))) hasPlaceOfOrigin = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("AlphanumericIdentificationOfThePackagingPlant"))) hasAlphanumericIdentificationOfThePackagingPlant = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("BlendsOfOliveOilAndOtherVegetableOils"))) hasBlendsOfOliveOilAndOtherVegetableOils = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("ColdExtraction"))) hasColdExtraction = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("FirstColdPressing"))) hasFirstColdPressing = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("Foodstuff"))) hasFoodstuff = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("HarvestingYear"))) hasHarvestingYear = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("IndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell"))) hasIndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("InformationOnTheSpecialStorageConditions"))) hasInformationOnTheSpecialStorageConditions = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("NonResealableOpeningSystem"))) hasNonResealableOpeningSystem = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("OilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives"))) hasOilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("OliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans"))) hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("OlivePomaceCategoryInformation"))) hasOlivePomaceCategoryInformation = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("OptionalReservedTerms"))) hasOptionalReservedTerms = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("VoluntaryLabellingParticulars"))) hasVoluntaryLabellingParticulars = true;
        }

        // source: Article 5(1)
        if (!hasLegalName) return false;
        // source: Article 5(1)
        if (!hasInformationOnTheSpecialStorageConditions) return false;
        // source: Article 5(1)
        if (!hasNonResealableOpeningSystem) return false;
        // source: Article 5(1)
        if (!hasOilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives) return false;
        // source: Article 5(2)
        if (hasPlaceOfOrigin && !hasLegalName) return false;
        // source: Article 5(2)
        if (hasPlaceOfOrigin && !hasLegalName) return false;
        // source: Article 5(3)
        if (hasBlendsOfOliveOilAndOtherVegetableOils) return false;
        // source: Article 5(3)
        if (hasColdExtraction) return false;
        // source: Article 5(3)
        if (hasFirstColdPressing) return false;
        // source: Article 5(3)
        if (hasFoodstuff) return false;
        // source: Article 5(3)
        if (hasHarvestingYear) return false;
        // source: Article 5(3)
        if (hasIndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell) return false;
        // source: Article 5(3)
        if (hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans) return false;
        // source: Article 5(3)
        if (hasOlivePomaceCategoryInformation) return false;
        // source: Article 5(3)
        if (hasOptionalReservedTerms) return false;
        // source: Article 5(3)
        if (hasVoluntaryLabellingParticulars) return false;

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
