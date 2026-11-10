// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract OlivePomaceOilCompliance {
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 1000; // source: Annex I, Table A, row 8
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 15000; // source: Annex I, Table A, row 8
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 1700; // source: Annex I, Table A, row 8
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 180; // source: Annex I, Table A, row 8
        if (keccak256(bytes(parameter)) == keccak256(bytes("PackagingCapacity"))) return value <= 5000; // source: Article 4(1)
        return true;
    }

    function checkLabelling(string[] memory items) public pure returns (bool) {
        bool hasMandatoryLabellingParticulars = false;
        bool hasInformationOnTheSpecialStorageConditions = false;
        bool hasAlphanumericIdentificationOfThePackagingPlant = false;
        bool hasNonResealableOpeningSystem = false;
        bool hasOlivePomaceCategoryInformation = false;

        for (uint i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) == keccak256(bytes("MandatoryLabellingParticulars"))) hasMandatoryLabellingParticulars = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("InformationOnTheSpecialStorageConditions"))) hasInformationOnTheSpecialStorageConditions = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("AlphanumericIdentificationOfThePackagingPlant"))) hasAlphanumericIdentificationOfThePackagingPlant = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("NonResealableOpeningSystem"))) hasNonResealableOpeningSystem = true;
            if (keccak256(bytes(items[i])) == keccak256(bytes("OlivePomaceCategoryInformation"))) hasOlivePomaceCategoryInformation = true;
        }

        return hasMandatoryLabellingParticulars && hasInformationOnTheSpecialStorageConditions && hasAlphanumericIdentificationOfThePackagingPlant && hasNonResealableOpeningSystem && hasOlivePomaceCategoryInformation;
    }

    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items) public pure returns (bool) {
        require(parameters.length == values.length, "Parameters and values length mismatch");

        for (uint i = 0; i < parameters.length; i++) {
            if (!checkLimit(parameters[i], values[i])) return false;
        }

        return checkLabelling(items);
    }
}
