// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VirginOliveOilCompliance {
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

        // source: Annex I, Table A, row 2
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 2000;
        // source: Annex I, Table A, row 2
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 20000;
        // source: Annex I, Table A, row 2
        if (keccak256(bytes(parameter)) == keccak256(bytes("K232"))) return value <= 2600;
        // source: Annex I, Table A, row 2
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 250;
        // source: Annex I, Table A, row 2
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 10;
        // source: Annex I, Table A, row 2
        if (keccak256(bytes(parameter)) == keccak256(bytes("MedianOfDefectMd"))) return value <= 3500;
        // source: Annex I, Table A, row 2
        if (keccak256(bytes(parameter)) == keccak256(bytes("FruityMedianMf"))) return value > 0;

        // source: Annex I, Table A, row 3
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value > 2000;
        // source: Annex I, Table A, row 3
        if (keccak256(bytes(parameter)) == keccak256(bytes("MedianOfDefectMd"))) return value > 3500;

        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 300;
        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 5000;
        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 1250;
        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 160;

        // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 1000;
        // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 15000;
        // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 1150;
        // source: Annex I, Table A, row 5
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 150;

        // source: Annex I, Table A, row 6
        // No limits set for crude olive-pomace oil

        // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 300;
        // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 5000;
        // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 2000;
        // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 200;

        // source: Annex I, Table A, row 8
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 1000;
        // source: Annex I, Table A, row 8
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 15000;
        // source: Annex I, Table A, row 8
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 1700;
        // source: Annex I, Table A, row 8
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 180;

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
            if (keccak256(bytes(items[i])) == keccak256(bytes("PlaceOfOrigin"))) hasPlaceOfOrigin = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("AlphanumericIdentificationOfThePackagingPlant"))) hasAlphanumericIdentificationOfThePackagingPlant = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("BlendsOfOliveOilAndOtherVegetableOils"))) hasBlendsOfOliveOilAndOtherVegetableOils = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("ColdExtraction"))) hasColdExtraction = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("FirstColdPressing"))) hasFirstColdPressing = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("Foodstuff"))) hasFoodstuff = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("HarvestingYear"))) hasHarvestingYear = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("IndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell"))) hasIndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("InformationOnTheSpecialStorageConditions"))) hasInformationOnTheSpecialStorageConditions = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("NonResealableOpeningSystem"))) hasNonResealableOpeningSystem = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("OilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives"))) hasOilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("OliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans"))) hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("OlivePomaceCategoryInformation"))) hasOlivePomaceCategoryInformation = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("OptionalReservedTerms"))) hasOptionalReservedTerms = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("VoluntaryLabellingParticulars"))) hasVoluntaryLabellingParticulars = true;
        }

        // source: Article 5(1)
        if (!hasLegalName) return false;
        // source: Article 5(1)
        if (!hasPlaceOfOrigin) return false;
        // source: Article 5(1)
        if (!hasAlphanumericIdentificationOfThePackagingPlant) return false;
        // source: Article 5(1)
        if (!hasNonResealableOpeningSystem) return false;
        // source: Article 5(1)
        if (!hasInformationOnTheSpecialStorageConditions) return false;

        // source: Article 5(2)
        if (!hasLegalName || !hasPlaceOfOrigin) return false;

        // source: Article 6(2)
        if (!hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans) return false;

        // source: Article 10, point (a)
        if (hasFirstColdPressing && !hasColdExtraction) return false;

        // source: Article 10, point (b)
        if (hasColdExtraction && !hasFirstColdPressing) return false;

        // source: Article 10, point (c)
        if (hasIndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell && !hasOliveOilObtainedDirectly
