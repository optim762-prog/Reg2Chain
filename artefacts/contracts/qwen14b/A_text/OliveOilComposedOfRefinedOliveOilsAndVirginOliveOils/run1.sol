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
        // No limit for other parameters
        return true;
    }

    // Labelling: `items` are the identifiers of the label items present on the label.
    // Returns false if a mandatory item is missing or a prohibited item is present.
    function checkLabelling(string[] memory items) public pure returns (bool) {
        // source: Article 5(1)
        bool hasLegalName = false;
        bool hasPlaceOfOrigin = false;
        bool hasAlphanumericIdentificationOfThePackagingPlant = false;
        bool hasBlendsOfOliveOilAndOtherVegetableOils = false;
        bool hasColdExtraction = false;
        bool hasFirstColdPressing = false;
        bool hasIndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell = false;
        bool hasInformationOnTheSpecialStorageConditions = false;
        bool hasNonResealableOpeningSystem = false;
        bool hasOliveOilObtainingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives = false;
        bool hasOlivePomaceCategoryInformation = false;
        bool hasVoluntaryLabellingParticulars = false;

        for (uint i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) == keccak256(bytes("LegalName"))) hasLegalName = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("PlaceOfOrigin"))) hasPlaceOfOrigin = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("AlphanumericIdentificationOfThePackagingPlant"))) hasAlphanumericIdentificationOfThePackagingPlant = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("BlendsOfOliveOilAndOtherVegetableOils"))) hasBlendsOfOliveOilAndOtherVegetableOils = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("ColdExtraction"))) hasColdExtraction = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("FirstColdPressing"))) hasFirstColdPressing = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("IndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell"))) hasIndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("InformationOnTheSpecialStorageConditions"))) hasInformationOnTheSpecialStorageConditions = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("NonResealableOpeningSystem"))) hasNonResealableOpeningSystem = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("OilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives"))) hasOliveOilObtainingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("OlivePomaceCategoryInformation"))) hasOlivePomaceCategoryInformation = true;
            else if (keccak256(bytes(items[i])) == keccak256(bytes("VoluntaryLabellingParticulars"))) hasVoluntaryLabellingParticulars = true;
        }

        // source: Article 5(1)
        if (!hasLegalName) return false;
        // source: Article 5(1)
        if (!hasAlphanumericIdentificationOfThePackagingPlant) return false;
        // source: Article 5(1)
        if (!hasInformationOnTheSpecialStorageConditions) return false;
        // source: Article 5(1)
        if (!hasNonResealableOpeningSystem) return false;
        // source: Article 5(1)
        if (!hasOliveOilObtainingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives) return false;

        // source: Article 3(1)
        if (hasBlendsOfOliveOilAndOtherVegetableOils) return false;

        // source: Article 10, point (a)
        if (hasFirstColdPressing && !hasColdExtraction) return false;

        // source: Article 10, point (b)
        if (hasColdExtraction && !hasFirstColdPressing) return false;

        // source: Article 10, point (c)
        if (hasIndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell) return false;

        // source: Article 10, point (d)
        if (hasIndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell) return false;

        // source: Article 8(2)
        if (hasPlaceOfOrigin) return false;

        // source: Article 9
        if (!hasAlphanumericIdentificationOfThePackagingPlant) return false;

        // source: Article 12(1)
        if (hasBlendsOfOliveOilAndOtherVegetableOils) return false;

        // source: Article 12(2)
        if (hasBlendsOfOliveOilAndOtherVegetableOils) return false;

        // source: Article 12(3)
        if (hasBlendsOfOliveOilAndOtherVegetableOils) return false;

        // source: Article 12(4)
        if (hasBlendsOfOliveOilAndOtherVegetableOils) return false;

        // source: Article 12(5)
        if (hasBlendsOfOliveOilAndOtherVegetableOils) return false;

        // source: Article 12(6)
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
