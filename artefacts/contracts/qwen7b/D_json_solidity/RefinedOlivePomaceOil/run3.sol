// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RefinedOlivePomaceOilCompliance {
    // Quality parameters
    string constant Acidity = "Acidity";
    string constant PeroxideValueMEqO2Kg = "PeroxideValueMEqO2Kg";
    string constant K268OrK270 = "K268OrK270";
    string constant DeltaK = "DeltaK";

    // Label items
    string constant AlphanumericIdentificationOfThePackagingPlant = "AlphanumericIdentificationOfThePackagingPlant";
    string constant ColdExtraction = "ColdExtraction";
    string constant FirstColdPressing = "FirstColdPressing";
    string constant Foodstuff = "Foodstuff";
    string constant HarvestingYear = "HarvestingYear";
    string constant OlivePomaceCategoryInformation = "OlivePomaceCategoryInformation";
    string constant OilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives = "OilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives";
    string constant OliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = "OliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans";
    string constant PlaceOfOrigin = "PlaceOfOrigin";

    // source: Annex I, Table A, row 7
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        if (keccak256(bytes(parameter)) == keccak256(bytes(Acidity))) return value <= 300;
        if (keccak256(bytes(parameter)) == keccak256(bytes(PeroxideValueMEqO2Kg))) return value <= 5000;
        if (keccak256(bytes(parameter)) == keccak256(bytes(K268OrK270))) return value <= 2000;
        if (keccak256(bytes(parameter)) == keccak256(bytes(DeltaK))) return value <= 200;
        return true; // No limit for this parameter
    }

    // source: Commission Delegated Regulation (EU) 2022/2104, Article 13
    function checkLabelling(string[] memory items) public pure returns (bool) {
        bool hasAlphanumericIdentificationOfThePackagingPlant = false;
        bool hasColdExtraction = false;
        bool hasFirstColdPressing = false;
        bool hasFoodstuff = false;
        bool hasHarvestingYear = false;
        bool hasOlivePomaceCategoryInformation = false;
        bool hasOilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives = false;
        bool hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = false;
        bool hasPlaceOfOrigin = false;

        for (uint i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) == keccak256(bytes(AlphanumericIdentificationOfThePackagingPlant))) hasAlphanumericIdentificationOfThePackagingPlant = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes(ColdExtraction))) hasColdExtraction = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes(FirstColdPressing))) hasFirstColdPressing = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes(Foodstuff))) hasFoodstuff = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes(HarvestingYear))) hasHarvestingYear = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes(OlivePomaceCategoryInformation))) hasOlivePomaceCategoryInformation = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes(OilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives))) hasOilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes(OliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans))) hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes(PlaceOfOrigin))) hasPlaceOfOrigin = true;
        }

        return hasAlphanumericIdentificationOfThePackagingPlant &&
               hasColdExtraction &&
               hasFirstColdPressing &&
               hasFoodstuff &&
               hasHarvestingYear &&
               hasOlivePomaceCategoryInformation &&
               hasOilComprisingExclusivelyOliveOilsThatHaveUndergoneRefiningAndOilsObtainedDirectlyFromOlives &&
               hasOliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans &&
               hasPlaceOfOrigin;
    }

    // Both checks together
    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items) public pure returns (bool) {
        require(parameters.length == values.length, "Parameters and values length mismatch");

        for (uint i = 0; i < parameters.length; i++) {
            if (!checkLimit(parameters[i], values[i])) return false;
        }

        return checkLabelling(items);
    }
}
