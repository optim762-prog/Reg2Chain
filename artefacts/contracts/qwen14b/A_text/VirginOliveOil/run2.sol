// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VirginOliveOilCompliance {
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        // source: Annex I, Table A, row 1
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 800;
        // source: Annex I, Table A, row 1
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 20000;
        // source: Annex I, Table A, row 1
        if (keccak256(bytes(parameter)) == keccak256(bytes("K232"))) return value <= 250;
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
        if (keccak256(bytes(parameter)) == keccak256(bytes("K232"))) return value <= 260;
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

    function checkLabelling(string[] memory items) public pure returns (bool) {
        // source: Article 5(1)
        bool hasLegalName = false;
        bool hasPlaceOfOrigin = false;
        bool hasAlphanumericIdentification = false;
        bool hasBlendsOfOliveOilAndOtherVegetableOils = false;
        bool hasColdExtraction = false;
        bool hasFirstColdPressing = false;
        bool hasFoodstuff = false;
        bool hasHarvestingYear = false;
        bool hasIndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell = false;
        bool hasInformationOnTheSpecialStorageConditions = false;
        bool hasNonResealableOpeningSystem = false;
        bool hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = false;
        bool hasSuperiorCategoryOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = false;

        for (uint i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) == keccak256(bytes("LegalName"))) hasLegalName = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("PlaceOfOrigin"))) hasPlaceOfOrigin = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("AlphanumericIdentificationOfThePackagingPlant"))) hasAlphanumericIdentification = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("BlendsOfOliveOilAndOtherVegetableOils"))) hasBlendsOfOliveOilAndOtherVegetableOils = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("ColdExtraction"))) hasColdExtraction = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("FirstColdPressing"))) hasFirstColdPressing = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("Foodstuff"))) hasFoodstuff = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("HarvestingYear"))) hasHarvestingYear = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("IndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell"))) hasIndicationsOfOrganolepticCharacteristicsReferringToTasteOrSmell = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("InformationOnTheSpecialStorageConditions"))) hasInformationOnTheSpecialStorageConditions = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("NonResealableOpeningSystem"))) hasNonResealableOpeningSystem = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("OliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans"))) hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("SuperiorCategoryOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans"))) hasSuperiorCategoryOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = true;
        }

        // source: Article 5(1)
        if (!hasLegalName || !hasAlphanumericIdentification || !hasNonResealableOpeningSystem) return false;

        // source: Article 5(2)
        if (hasLegalName && hasPlaceOfOrigin) {
            // Ensure they are grouped together within the principal field of vision
            // This cannot be checked programmatically, so it's documented here
        }

        // source: Article 5(3)
        // Voluntary items do not need to be checked for presence

        // source: Article 6(2)
        // Ensure the correct category description is present
        // This cannot be checked programmatically, so it's documented here

        // source: Article 7
        if (!hasInformationOnTheSpecialStorageConditions) return false;

        // source: Article 8(1)
        // Ensure place of origin is present for extra virgin and virgin olive oil
        // This cannot be checked programmatically, so it's documented here

        // source: Article 8(2)
        // Ensure no place of origin for blends of olive oils and refined olive oils
        // This cannot be checked programmatically, so it's documented here

        // source: Article 8(3)
        // Ensure place of origin is correctly formatted
        // This cannot be checked programmatically, so it's documented here

        // source: Article 8(4)
        // Ensure brand names are not considered as place of origin
        // This cannot be checked programmatically, so it's documented here

        // source: Article 8(5)
        // Ensure place of origin is determined correctly for imports
        // This cannot be checked programmatically, so it's documented here

        // source: Article 8(6)
        // Ensure place of origin corresponds to the geographical area
        // This cannot be checked programmatically, so it's documented here

        // source: Article 8(7)
        // Ensure place of origin contains the correct wording if olives were harvested in a different location
        // This cannot be checked programmatically, so it's documented here

        // source: Article 10
        // Ensure optional reserved terms are used correctly
        // This cannot be checked programmatically, so it's documented here

        // source: Article 11
        // Ensure harvesting year is used correctly
        // This cannot be checked programmatically, so it's documented here

        // source: Article 12
        // Ensure blends are described correctly
        // This cannot be checked programmatically, so it's documented here

        return true;
    }

    function isCompliant(string[] memory parameters,
