// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RefinedOlivePomaceOilCompliance {
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 300; // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 160; // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("FattyAcidEthylEstersMgKg"))) return value <= 35000; // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("FruityMedianMf"))) return value > 0; // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("K232"))) return value <= 2500; // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 2000; // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("MedianOfDefectMd"))) return value <= 180; // source: Annex I, Table A, row 7
        if (keccak256(bytes(parameter)) == keccak256(bytes("PackagingCapacity"))) return value <= 5000; // source: Article 4(1)
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 5000; // source: Annex I, Table A, row 7
        return true;
    }

    function checkLabelling(string[] memory items) public pure returns (bool) {
        bool hasLegalName = false;
        bool hasPlaceOfOrigin = false;
        bool hasAlphanumericIdentificationOfThePackagingPlant = false;
        bool hasOlivePomaceCategoryInformation = false;
        bool hasOptionalReservedTerms = false;

        for (uint i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) == keccak256(bytes("LegalName"))) hasLegalName = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("PlaceOfOrigin"))) hasPlaceOfOrigin = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("AlphanumericIdentificationOfThePackagingPlant"))) hasAlphanumericIdentificationOfThePackagingPlant = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("OlivePomaceCategoryInformation"))) hasOlivePomaceCategoryInformation = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("OptionalReservedTerms"))) hasOptionalReservedTerms = true;
        }

        return hasLegalName && hasPlaceOfOrigin && hasAlphanumericIdentificationOfThePackagingPlant && hasOlivePomaceCategoryInformation && !hasOptionalReservedTerms;
    }

    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items) public pure returns (bool) {
        require(parameters.length == values.length, "Parameters and values arrays must have the same length");

        for (uint i = 0; i < parameters.length; i++) {
            if (!checkLimit(parameters[i], values[i])) return false;
        }

        return checkLabelling(items);
    }
}
